import re
from pathlib import Path
import logging

import ffmpeg
import requests

from bs4 import BeautifulSoup


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="{asctime} [{levelname}] {message}",
                                  datefmt="%Y-%m-%d %H:%M:%S",
                                  style="{")
    hf = logging.FileHandler("log_xvdl.log")
    hf.setFormatter(formatter)
    sf = logging.StreamHandler()
    sf.setFormatter(formatter)
    logger.addHandler(hf)
    logger.addHandler(sf)
    return logger


logger = get_logger()


def find_from_string(pattern: str, text: str) -> str:
    find = re.search(pattern, text)
    if find:
        return find.group()
    else:
        raise ValueError(f"Pattern not found in response.")


def get_video_name(response_text: str) -> str:
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
    if "/prof-video-click/" in url:
        return find_from_string(r"(?<=/)\d{5,}(?=/)", url)
    else:
        return find_from_string(r"(?<=video)\d+(?=/)", url)


def get_url_hls(response_text: str) -> str:
    return find_from_string(pattern=r"(?<=setVideoHLS\(['\"]).+(?=['\"]\))",
                            text=response_text.strip())


def get_resolution(string: str) -> str:
    return int(find_from_string(pattern=r"(?<=-)\d+(?=p-)",
                                text=string))


def get_second_hls(response: str) -> str:
    items_raw = [item for item in response.split("\n") if ".m3u8" in item]

    items_list = []
    for item in items_raw:
        items_list.append((get_resolution(item), item))

    items_list.sort(reverse=True)
    # Seleccionamos el item con mejor resolución
    second_hls = items_list[0][1]
    return second_hls


def download_m3u8(url_m3u8: str, name_dir: str, name_video: str,
                  video_id: str, overwrite=False) -> None:

    filename = f"{name_dir}{name_video}{video_id}.mp4"

    if not Path(filename).exists():
        logger.info(f"Download: {filename}")
        stream = ffmpeg.input(url_m3u8).output(
            filename, codec="copy", loglevel="quiet")

        stream.run()
        logger.info("Done!")
    elif overwrite:
        logger.info(f"Overwrite: {filename}")
        stream.run(overwrite_output=overwrite)
        logger.info("Done!")
    else:
        logger.warning(f"SKIP {filename} was already downloaded.")


def main():
    NAME_DIR = "xvideos/"
    Path(NAME_DIR).mkdir(parents=True, exist_ok=True)

    URL1 = "https://www.xvideos.com/video28518201/_"
    URL2 = "https://www.xvideos.com/video19411781/_"
    URL_1440 = "https://www.xvideos.com/video67812787/sex_1_"
    URL_10 = "https://www.xvideos.com/video72704365/_desfloracion_mujer_joven_virgen_cristalina_y_sus_sucios_deseos_casting_18_anos"
    URL_20 = "https://www.xvideos.com/video26834439/defloracion_tubo_en_u"

    response = requests.get(URL_10)

    video_id = get_video_id(URL_10)
    name_video = get_video_name(response.text)
    first_url_hls = get_url_hls(response.text)

    first_hls_response = requests.get(first_url_hls)

    sufix = get_second_hls(response=first_hls_response.text)
    second_url_hls = re.sub("hls.m3u8", sufix, first_url_hls)

    download_m3u8(url_m3u8=second_url_hls,
                  name_dir=NAME_DIR,
                  name_video=name_video,
                  video_id=video_id)


if __name__ == "__main__":
    main()
