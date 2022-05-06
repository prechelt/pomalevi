"""Knows about HTML generation."""
import datetime as dt
import os
import shutil
import typing as tg

from pmlv.base import Stoptimes


def default_css_srcfile():
    return "%s/../css/pomalevi.css" % os.path.dirname(__file__)


def default_favicon_srcfile():
    return f"{os.path.dirname(__file__)}/../img/favicon.png"


html_template = """
<!DOCTYPE html>
<html>
  <head>
    <title>%(title)s</title>
    %(css_block)s
    <link rel="icon" type="image/png" href="%(favicon)s">
    <meta charset="UTF-8">
  </head>
  <body>

    <h1 class="pmlv-title">%(title)s</h1>

    <video id="pomalevi-video" class="pmlv-video"
           height=540 controls
           data-setup='{ "playbackRates": [0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.4, 1.7, 2.0] }'>>
       Your browser does not support the video tag.
    </video>

    <br>
    <button class="pmlv-button" onclick="pmlv_skip(pmlv_video, -10)">-10s</button>
    <button class="pmlv-button" onclick="pmlv_skip(pmlv_video, 10)">+10s</button>
    --
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.6)">0.6x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.7)">0.7x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 0.85)">0.85x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.0)">1.0x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.2)">1.2x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.4)">1.4x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 1.7)">1.7x</button>
    <button class="pmlv-button" onclick="pmlv_speed(pmlv_video, 2.0)">2.0x</button>

    <table class="pmlv-table">
      %(toc_rows)s
    </table>

    <footer class="pmlv-footer">
      <p>Generated %(date)s 
         by <a href="https://github.com/prechelt/pomalevi">pomalevi</a> &mdash;
         Powerpoint-based maintainable lecture videos.
      </p>
    </footer>

    %(script)s

  </body>

</html>
"""

script_template = """
    <script>
      var pmlv_video = document.getElementById("pomalevi-video")
      var pmlv_video_idx = 1
      var pmlv_stoptimes = %(stoptimes)s  // list of list of floats: stop times in seconds

      function pmlv_pause_at_stoptimes() {
          for (var t of pmlv_stoptimes[pmlv_video_idx-1]) {
            if(pmlv_video.currentTime >= t && pmlv_video.currentTime <= t+0.6) {
              // 0.6s suffices even for Firefox at 2.0x speed. 0.5s does not.
              pmlv_video.pause()
              pmlv_video.currentTime += 0.6
            }
          }
      }

      function pmlv_skip(obj, secs) {
        obj.currentTime += secs
      }

      function pmlv_speed(obj, factor) {
        obj.playbackRate = factor
      }

      function pmlv_switch_to(i, play=true) {
        pmlv_video.src = "v" + i + ".%(suffix)s"
        pmlv_video_idx = i  // select the relevant stoptimes
        pmlv_video.load()
        if (play) {
          pmlv_video.play()
        }
      }

      pmlv_video.addEventListener("timeupdate", pmlv_pause_at_stoptimes)
      pmlv_switch_to(1, false)

    </script>
"""


def read_toc(tocfile: str, numvideos: int) -> tg.Tuple[str, tg.List[str]]:
    with open(tocfile, 'rt') as f:
        all = f.read()
    items = all.split('\n\n')
    title, items = items[0], items[1:]
    if len(items) < numvideos:
        items.extend((numvideos - len(items)) * [''])  # add items if too few
    return title, items[:numvideos]


def generate_html(title: str, 
                  cssfile: tg.Optional[str], cssurl: tg.Optional[str],
                  stoptimes: Stoptimes, suffix: str,
                  toc: tg.List[str], outputdir: str):
    # https://html.spec.whatwg.org/multipage/media.html
    filename = f"{outputdir}/index.html"
    print(f"Generating {filename}")
    favicon_srcfile = default_favicon_srcfile()
    favicon_href = "favicon.png"
    date = dt.datetime.now().strftime("%Y-%m-%d")
    #----- prepare CSS block:
    if cssfile is None and cssurl is None:  # copy pomalevi default CSS
        css_srcfile = default_css_srcfile()
        css_href = "pomalevi.css"
    elif cssfile:  # copy given file
        css_srcfile = cssfile
        css_href = os.path.basename(cssfile)
    elif cssurl:
        css_srcfile = None
        css_href = cssurl
    css_block = f'    <link rel="stylesheet" href="{css_href}">'
    #----- prepare TOC:
    toc_rows = ""
    script = script_template % dict(stoptimes=stoptimes, suffix=suffix)
    for i in range(1, len(stoptimes)+1):
        as_link = f"onclick='pmlv_switch_to({i})'"
        num_cell = f"{i}"
        toc_cell = toc[i-1]
        toc_row = (f"\n      <tr class='pmlv-tablerow' {as_link}>"
                   f"<td class='pmlv-numcell'>{num_cell}</td>"
                   f"<td>{toc_cell}</td></tr>")
        toc_rows += toc_row
    #----- generate HTML:
    html = html_template % dict(title=title, 
                                favicon=favicon_href, 
                                css_block=css_block, 
                                toc_rows=toc_rows, date=date, script=script)
    #----- fill outputdir:
    with open(filename, 'wt', encoding='utf8') as f:
        f.write(html)
    shutil.copyfile(favicon_srcfile, f"{outputdir}/{favicon_href}")
    if css_srcfile:
        shutil.copyfile(css_srcfile, f"{outputdir}/{css_href}")
