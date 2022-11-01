import re
import requests
import time
from glob import glob
from pathlib import Path
from typing import List, Optional

import typer
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from utils import logger
from utils import (get_video_name, get_video_id,
                   get_url_hls, get_second_hls, download_m3u8)


app = typer.Typer(name="xvdl",
                  help="CLI to download videos.",
                  add_completion=True)


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
    with logging_redirect_tqdm(loggers=[logger]):
        logger.info("Start new run!!!")

        if file:
            urls = file.readlines()

        assert urls, typer.BadParameter("No urls were provided.")

        name_dir.mkdir(parents=True, exist_ok=True)
        videos_names = glob(f"{str(name_dir.absolute())}/*")
        videos_names = " ".join(videos_names)

        logger.info(f"Number of urls: {len(urls)}")

        for idx, url in enumerate(tqdm(urls, colour="green"), start=1):
            video_id = get_video_id(url)

            logger.info(f"Request to {idx}.- {url}")

            if not video_id in videos_names:

                response = requests.get(url)
                name_video = get_video_name(response.text)
                first_url_hls = get_url_hls(response.text)

                logger.info(f"File name: {name_video}{video_id}.mp4")

                first_hls_response = requests.get(first_url_hls)

                sufix = get_second_hls(response=first_hls_response.text)
                second_url_hls = re.sub("hls.m3u8", sufix, first_url_hls)
                try:
                    download_m3u8(url_m3u8=second_url_hls,
                                  name_dir=name_dir,
                                  name_video=name_video,
                                  video_id=video_id,
                                  overwrite=overwrite)
                except:
                    logger.exception(
                        "An error occurred while downloading file.")

            else:
                logger.warning(f"SKIP! {video_id} was already downloaded.")
                time.sleep(0.1)

        logger.info("Finish to run!!!\n")


if __name__ == "__main__":
    app()

    URL1 = "https://www.xvideos.com/video28518201/_"
    URL2 = "https://www.xvideos.com/video19411781/_"
    URL_1440 = "https://www.xvideos.com/video67812787/sex_1_"
    URL_10 = "https://www.xvideos.com/video72704365/_desfloracion_mujer_joven_virgen_cristalina_y_sus_sucios_deseos_casting_18_anos"
    URL_20 = "https://www.xvideos.com/video26834439/defloracion_tubo_en_u"
