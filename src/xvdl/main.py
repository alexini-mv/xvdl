import re
import requests
import time
from pathlib import Path
from typing import List, Optional

import typer
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from utils import logger
from utils import (get_video_name, get_video_id,
                   get_url_hls, get_second_hls, download_m3u8)


# Instanciamos el manejador del CLI
app = typer.Typer(name="xvdl",
                  help="CLI to download videos.",
                  add_completion=True)


# Definimos el comando del CLI, así como los argumentos del comando
# y las opciones
@app.command(help="CLI to download videos.")
def main(urls: List[str] = typer.Argument(None,
                                          help="URLs to download.",
                                          show_default=False),
         name_dir: Optional[Path] = typer.Option("xvideos/",
                                                 "-d",
                                                 "--destination",
                                                 help="Destination to save the downloaded videos.",
                                                 rich_help_panel="CLI Options"),
         file: typer.FileText = typer.Option(None,
                                             "-f",
                                             "--file-urls",
                                             help="File text with urls.",
                                             show_default=None,
                                             rich_help_panel="CLI Options"),
         overwrite: bool = typer.Option(False,
                                        "-w",
                                        "--overwrite",
                                        help="Overwrite the exist video files.",
                                        show_default=None,
                                        rich_help_panel="CLI Options")
         ):
    # Hamos que la salida del logger se redirija al writer de tqdm
    with logging_redirect_tqdm(loggers=[logger]):
        logger.info("Start new run!!!")

        # Verificamos si se proporcionó un archivo de texto
        if file:
            # Guardamos el contenido del archivo en la variable urls
            urls = list(map(lambda x: x.strip(), file.readlines()))

        # Nos aseguramos que urls no esté vacio.
        assert urls, typer.BadParameter("No urls were provided.")

        # Creamos o verificamos que exista el directorio donde se
        # guardarán los videos
        name_dir.mkdir(parents=True, exist_ok=True)

        # Generamos un string con el nombre de los videos ya descargados
        videos_names = map(lambda x: x.name, name_dir.glob("*"))
        videos_names = " ".join(videos_names)

        # Iteramos sobre toda la lista de urls
        for idx, url in enumerate(tqdm(urls, colour="green"), start=1):
            # Obtenemos el id del video a partir de la url
            video_id = get_video_id(url)

            logger.info(f"Request to {idx}/{len(urls)}: {url}")

            # Verificamos que el video no ha sido descargado antes.
            if not video_id in videos_names:
                # Hacemos la petición GET a la url.
                # ========== Falta implementar el proxy aleatorio!!! ==========
                response = requests.get(url)

                # Construimos el nombre del video que se descargará
                name_video = get_video_name(response.text)
                # Obtenemos la url del primer archivo m3u8
                first_url_hls = get_url_hls(response.text)

                logger.info(f"File name: {name_video}{video_id}.mp4")
                # Hacemos la petición a la url del m3u8 para obtener la
                # resoluciones,
                first_hls_response = requests.get(first_url_hls)

                # Obtenemos la mejor resolución de video y el nombre del
                # archivo m3u8
                resolution, sufix = get_second_hls(
                    response=first_hls_response.text)

                # Construimos la segunda url del archivo verdadero para
                # descargar el video
                second_url_hls = re.sub(r"hls.m3u8.*", sufix, first_url_hls)

                try:
                    # Descargamos el video a partir de la segunda url
                    download_m3u8(url_m3u8=second_url_hls,
                                  name_dir=name_dir,
                                  name_video=name_video,
                                  video_id=video_id,
                                  overwrite=overwrite,
                                  resolution=resolution)
                except:
                    logger.exception(
                        "An error occurred while downloading file.")
            else:
                # Si el video ya ha sido descargado antes, se salta esa url
                logger.warning(f"SKIP! {video_id} was already downloaded.\n")
                time.sleep(0.1)

        logger.info("Finish to run!!!\n")


if __name__ == "__main__":
    app()
