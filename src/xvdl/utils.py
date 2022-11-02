import re
from pathlib import Path
from typing import Tuple

import ffmpeg
from bs4 import BeautifulSoup

from configlogger import setup_logger
logger = setup_logger()


def find_from_string(pattern: str, text: str) -> str:
    """Función genérica para encontrar un substring a partir de un patrón
    descrito como una expresión regular"""
    find = re.search(pattern, text)
    if find:
        return find.group()
    else:
        raise ValueError(f"Pattern not found in response.")


def get_video_name(response_text: str) -> str:
    """Buscamos los elementos para construir el nombre del video, a partir del
    response de la petición GET de la url"""
    s = BeautifulSoup(response_text, "html.parser")
    elements = s.find('div', class_=re.compile('video-tags-list'))
    channel = elements.find('a', class_=re.compile('label main'))
    pstars = elements.find_all('a', class_=re.compile('label profile'))

    if pstars:
        video_name = ""
        for star in pstars:
            video_name += f"{star.text.replace(' ', '_')}-"
    elif channel:
        video_name = f"{channel.text.replace(' ', '_')}-channel-"
    else:
        video_name = f"z_amateur-"
    return video_name


def get_video_id(url: str) -> str:
    """Obtenemos el id del video a partir de la url"""
    if "/prof-video-click/" in url:
        return find_from_string(r"(?<=/)\d{5,}(?=/)", url)
    else:
        return find_from_string(r"(?<=video)\d+(?=/)", url)


def get_url_hls(response_text: str) -> str:
    """Buscamos la url del primer archivo m3u8 a partir del response de la
    primera petición GET"""
    return find_from_string(pattern=r"(?<=setVideoHLS\(['\"]).+(?=['\"]\))",
                            text=response_text.strip())


def get_resolution(string: str) -> str:
    """Obtenemos la resolución con una expresión regular"""
    return int(find_from_string(pattern=r"(?<=-)\d+(?=p)",
                                text=string))


def get_second_hls(response: str) -> Tuple[str, str]:
    """Buscamos el nombre del archivo .m3u8 para descargar el video con 
    mejor resolución"""
    items_raw = [item for item in response.split("\n") if ".m3u8" in item]

    items_list = []
    for item in items_raw:
        items_list.append((get_resolution(item), item))

    items_list.sort(reverse=True)
    # Seleccionamos el item con mejor resolución
    return items_list[0]


def download_m3u8(url_m3u8: str, name_dir: Path, name_video: str,
                  video_id: str, overwrite: bool = False,
                  resolution: str = None) -> None:
    """Descargamos el video a partir del archivo m3u8 con la mejor resolución"""
    # Construimos la ruta donde se guardará el video descargado
    filename = name_dir / f"{name_video}{video_id}.mp4"

    # Verificamos si el archivo no existe para descargarlo
    if not filename.exists():
        logger.info(f"Download video: {str(filename.absolute())}")
        # Definimos la tarea de descarga mediante ffmpeg
        stream = ffmpeg.input(url_m3u8).output(str(filename.absolute()),
                                               codec="copy",
                                               loglevel="quiet")
        try:
            # Intentamos ejecutar la tarea de descarga
            stream.run(capture_stderr=True)
        except ffmpeg._run.Error as e:
            # Si existe un error, lo imprime en pantalla
            print(f"STDOUT:\t{e.stdout}")
            print(f"STDERR:\t{e.stderr}")
    elif overwrite:
        # Si el archivo existe, y además queremos sobreescribirlo.
        logger.info(f"Overwrite: {str(filename.absolute())}")
        stream.run(overwrite_output=overwrite)
    else:
        # Si existe el archivo y no queremos sobreescribirlo, lo saltamos
        logger.warning(f"SKIP! {filename} was already downloaded.")

    # Imprimimos la resolución y el tamaño del archivo
    logger.info(f"Video Resolution: {resolution}p. \tVideo Size : {filename.stat().st_size / 1024 ** 2:.2f} MB.\n")
