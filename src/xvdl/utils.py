import re
import ffmpeg
from pathlib import Path
from bs4 import BeautifulSoup

from configlogger import setup_logger
logger = setup_logger()


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


def download_m3u8(url_m3u8: str, name_dir: Path, name_video: str,
                  video_id: str, overwrite=False) -> None:

    filename = name_dir / f"{name_video}{video_id}.mp4"

    if not filename.exists():
        logger.info(f"Download video: {str(filename.absolute())}")

        stream = ffmpeg.input(url_m3u8).output(str(filename),
                                               codec="copy",
                                               loglevel="quiet")

        stream.run()
    elif overwrite:
        logger.info(f"Overwrite: {str(filename.absolute())}")
        stream.run(overwrite_output=overwrite)
    else:
        logger.warning(f"SKIP! {filename} was already downloaded.")

    logger.info(f"Video Size : {filename.stat().st_size / 1024 ** 2:.2f} MB.")
    print("")
