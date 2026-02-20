import logging
import webbrowser
import dataclasses as dc
from urllib.parse import urljoin
import requests
import regex as re
import pandas as pd
from bs4 import BeautifulSoup


log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


@dc.dataclass
class Parser:
    user: str
    base_url: str = dc.field(init=False)
    movies: list[dict[str, str]] = dc.field(init=False, default_factory=list)

    def __post_init__ (self) -> None:
        self.base_url = f"https://filmow.com/usuario/{self.user}/filmes/ja-vi/"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) filmow_to_letterboxd/1.0"
        })

        self.parse()
        self.write_csv_files()

    def get_last_page (self) -> int:
        last_page = 1
        source_code = self.session.get(self.base_url, timeout=20).text
        soup = BeautifulSoup(source_code, "html.parser")

        pag_div = soup.find("div", class_="pagination")
        if not pag_div:
            return last_page

        for a in pag_div.find_all("a", href=True):
            match = re.search(r"[?&]pagina=(\d+)", a["href"])
            if match:
                last_page = max(last_page, int(match.group(1)))

        return last_page

    def parse (self) -> None:
        curr_page = 1
        last_page = self.get_last_page()
        log.info(f"Iniciando importação: {last_page} página(s) encontrada(s).")

        while curr_page <= last_page:
            url = f"{self.base_url}?pagina={curr_page}"
            response = self.session.get(url, timeout=20)
            soup = BeautifulSoup(response.text, "html.parser")

            h1 = soup.find("h1")
            if response.status_code >= 400 or (h1 and "não encontrada" in h1.get_text(strip=True).lower()):
                log.info(f"Erro ao tentar acessar a {curr_page}-ésima página do ja-vi.")
                raise Exception

            movies_ul = soup.find("ul", id="movies-list")
            if not movies_ul:
                log.info(f"Página {curr_page}/{last_page}: sem filmes encontrados.")
                curr_page += 1
                continue

            page_movies = 0
            saved_movies = 0
            for movie in movies_ul.find_all("li"):
                anchor = movie.find("a", class_="tip-movie")
                if not anchor or not anchor.get("href"):
                    continue

                movie_href = anchor["href"]
                rating = None

                star_span = movie.find("span", class_="star-rating")
                if star_span and star_span.get("title"):
                    m = re.search(r"([0-5](?:[.,]5)?)", star_span["title"])
                    if m:
                        rating = m.group(1).replace(",", ".")

                if self.parse_movie(movie_href, rating):
                    saved_movies += 1
                page_movies += 1

            log.info(
                f"Página {curr_page}/{last_page} concluída: "
                f"{page_movies} lido(s), {saved_movies} salvo(s), total {len(self.movies)}."
            )

            curr_page += 1

    def parse_movie (self, movie_title, rating: str | None) -> bool:
        log.debug(f"Iniciando leitura do filme {movie_title}")

        movie_url = urljoin("https://filmow.com", movie_title)
        source_code = self.session.get(movie_url, timeout=20).text
        soup = BeautifulSoup(source_code, "html.parser")

        try:
            title = None
            title_h1 = soup.select_one("h1.movie__title")
            if title_h1:
                title = title_h1.get_text(" ", strip=True)
                year_span = title_h1.select_one("span.movie__year")
                if year_span:
                    title = title.replace(year_span.get_text(" ", strip=True), "").strip()

            if not title:
                movie_profile = soup.find("div", class_="movie-profile")
                if movie_profile:
                    title_div = movie_profile.find("div", class_="movie-title")
                    if title_div and title_div.find("h1"):
                        title = title_div.find("h1").get_text(strip=True)

            original_name = soup.select_one("h3.movie__original-title")
            if original_name:
                title = original_name.get_text(strip=True)
            else:
                old_original_name = soup.find("h2", class_="movie-original-title")
                if old_original_name is not None:
                    title = old_original_name.get_text(strip=True)

            if not title:
                return False

            director = None
            director_names = []

            for info_block in soup.select("div.movie__info-label"):
                heading = info_block.find("h3")
                if heading and "dirigido por" in heading.get_text(" ", strip=True).lower():
                    director_names = [
                        a.get_text(strip=True)
                        for a in info_block.select("a")
                        if a.get_text(strip=True)
                    ]
                    if director_names:
                        break

            if not director_names:
                mobile_heading = soup.select_one("div.movie__mobile-directors h3")
                if mobile_heading and "dirigido por" in mobile_heading.get_text(" ", strip=True).lower():
                    director_names = [
                        a.get_text(strip=True)
                        for a in soup.select('div.movie__mobile-directors a.movie__genre')
                        if a.get_text(strip=True)
                    ]

            if not director_names:
                director_names = [
                    span.get_text(strip=True)
                    for span in soup.select('div.directors a span[itemprop="name"]')
                    if span.get_text(strip=True)
                ]
            if director_names:
                director = ", ".join(dict.fromkeys(director_names))

            release = None
            title_year = soup.select_one("h1.movie__title span.movie__year")
            if title_year:
                year_match = re.search(r"\b(\d{4})\b", title_year.get_text(strip=True))
                if year_match:
                    release = year_match.group(1)
            if not release:
                title_tag = soup.find("title")
                if title_tag:
                    year_match = re.search(r"\b(\d{4})\b", title_tag.get_text(" ", strip=True))
                    if year_match:
                        release = year_match.group(1)
            if not release:
                old_release_tag = soup.select_one("div.movie-title small.release")
                if old_release_tag:
                    year_match = re.search(r"\b(\d{4})\b", old_release_tag.get_text(" ", strip=True))
                    if year_match:
                        release = year_match.group(1)

            self.movies.append({
                "Title": title,
                "Directors": director,
                "Year": release,
                "Rating": rating,
            })
            return True

        except Exception:
            log.debug(f"Erro tentando ler o filme referente a {movie_title}")
            return False

    def write_csv_files (self) -> None:
        df = pd.DataFrame(self.movies, columns=["Title", "Directors", "Year", "Rating"])

        curr_file = 1
        start_index = 0
        end_index = min(1900, len(self.movies))

        while end_index < len(self.movies):
            df[ start_index : end_index ].to_csv(
                f"{curr_file}{self.user}.csv", index=False, encoding="UTF-8"
            )

            start_index = end_index
            end_index = min(start_index + 1900, len(self.movies))
            curr_file += 1

        df[ start_index : end_index ].to_csv(
            f"{curr_file}{self.user}.csv", index=False, encoding="UTF-8"
        )
        log.info(f"Exportação concluída: {curr_file} arquivo(s) CSV gerado(s).")


if __name__ == "__main__":
    try:
        username = input('Digite seu nome de usuário do Filmow: ')
        print("Importação iniciada. Acompanhe o progresso abaixo:")
        Parser(username.lower().strip())

    except Exception:
        print(f"Usuário {username} não encontrado. Tem certeza que digitou certo?")
        username = input("Digite seu nome de usuário do Filmow: ")
        Parser(username.lower().strip())

    msg = """
    Pronto!
    Siga para https://letterboxd.com/import/, SELECT A FILE, 
    escolha o arquivo CSV gerado e PRONTO!

    """
    print(msg)


