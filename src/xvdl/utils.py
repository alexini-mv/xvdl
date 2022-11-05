import re
from random import choice
from pathlib import Path
from typing import List, Dict, Union

import ffmpeg
from bs4 import BeautifulSoup

from .configlogger import setup_logger
logger = setup_logger()


def get_a_proxy(proxies: Union[List[str], None]) -> Union[Dict[str, str], None]:
    if proxies:
        url = choice(proxies)
        return {"http": url}
    else:
        return None


def find_from_string(pattern: str, text: str) -> str:
    """Función genérica para encontrar un substring a partir de un patrón
    descrito como una expresión regular"""
    find = re.search(pattern, text)
    if find:
        return find.group()
    else:
        logger.error(f"Pattern not found in response.")
        raise ValueError(f"Pattern not found in response.")


def get_video_name(response_text: str) -> str:
    """Buscamos los elementos para construir el nombre del video, a partir del
    response de la petición GET de la url"""
    s = BeautifulSoup(response_text, "html.parser")
    elements = s.find('div', class_=re.compile('video-tags-list'))
    channel = elements.find('a', class_=re.compile('label main')
                            ).find('span', class_=re.compile('name'))
    pstars = elements.find_all('a', class_=re.compile('label profile'))

    if pstars:
        pstars = map(lambda x: x.find('span', class_=re.compile('name')),
                     pstars)
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


def get_second_hls(response: str) -> str:
    """Buscamos el nombre del archivo .m3u8 para descargar el video con 
    mejor resolución"""
    items_raw = [item for item in response.split("\n") if ".m3u8" in item]

    items_list = []
    for item in items_raw:
        items_list.append((get_resolution(item), item))

    items_list.sort(reverse=True)
    # Seleccionamos el item con mejor resolución
    return items_list[0][1]

def get_info_video(filename: Path) -> str:
    video_resolution = ffmpeg.probe(filename)["streams"][0]["height"]
    video_size = filename.stat().st_size / 1024 ** 2
    return f"Video Resolution: {video_resolution}p\tVideo Size : {video_size:.2f} MB\n"

def download_m3u8(url_m3u8: str, name_dir: Path, name_video: str,
                  video_id: str, overwrite: bool = False) -> None:
    """Descargamos el video a partir del archivo m3u8 con la mejor resolución"""
    # Construimos la ruta donde se guardará el video descargado
    filename = name_dir / f"{name_video}{video_id}.mp4"

    # Verificamos si el archivo no existe para descargarlo
    if not filename.exists() or overwrite:
        logger.info(f"Download video: {str(filename)}")
        # Definimos la tarea de descarga mediante ffmpeg
        stream = ffmpeg.input(url_m3u8).output(str(filename.absolute()),
                                               codec="copy",
                                               loglevel="quiet")
        try:
            # Si el archivo existe, y además queremos sobreescribirlo.
            if filename.exists() and overwrite:
                logger.warning(f"Overwrite: {str(filename)}")
            
            # Intentamos ejecutar la tarea de descarga
            stream.run(capture_stderr=True, overwrite_output=overwrite)

        except ffmpeg._run.Error as e:
            # Si existe un error, lo imprime en pantalla
            print(f"STDOUT:\t{e.stdout}")
            print(f"STDERR:\t{e.stderr}")
    else:
        # Si existe el archivo y no queremos sobreescribirlo, lo saltamos
        logger.warning(f"SKIP! {filename} was already downloaded.")

    # Imprimimos la resolución y el tamaño del archivo
    logger.info(get_info_video(filename))
