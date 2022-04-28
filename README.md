# pomalevi

PowerPoint-based maintainable lecture videos tool


## What `pomalevi` is

PowerPoint allows recording slide shows 
with narration and even a webcam insert
with its SlideShow⟶RecordSlideShow function.
The media files are stored within the PPT file on a per-slide basis.
This can be turned into a video via "File⟶SaveAs⟶*.wmv"

pomalevi converts such a video file (or any other) as follows:

- it turns the huge video produced by PowerPoint into a _much_ smaller one
  by applying more reasonable compression settings
- it can split the video into parts (separate, shorter videos) based on 
  when a user-defined `splitlogo` appears in the video
- it produces a simple HTML page with table of content hyperlinks for these
  parts based on a trivial text file containing parts descriptions
- it provides a very simple HTML player that will stop the video
  when a user-defined `stoplogo` appears in the video,
  so that the audience can ponder a question.


## Why `pomalevi` exists

I have previously used Camtasia to record lecture videos with Camtasia's
PowerPoint plugin.
I have inserted the stops I wanted (after I'd asked the viewers a question)
manually in the Camtasia Editor and then cut the video
into the five-or-so pieces (of 10-20 minutes each) I want 
and exported ("produced") each piece individually using the Batch Production
feature.

This gives nice results, but is a lot of manual work. 
It is acceptable for a one-time process, but what if I want to modify 
two of the slides next year? Or modify my narration? Aw!

PowerPoint's "Record" function is a good answer to this:
Each slide can be re-recorded individually.
Then just re-export the whole video.

But I did not want to give up my chopping-into-five-parts
and even less so the automated stops that Camtasia's SmartPlayer allows.
That's when the idea of pomalevi was born:
Let's combine the strengths of PowerPoint's slidewise recording 
with fully automated postprocessing.
A couple of couples of hours later here we go.


## Pros and cons

Pro:
- Pomalevi-plus-Powerpoint produces very useful output with little effort
- Subsequent changes are easy to make, your lecture videos become maintainable

Con:
- Depending on how fast your computer is, re-creating a pomalevi video
  takes a substantial amount of time during which your machine is very busy.

In my case, it is typically about 1.5x the video play time,
the bigger part of which is needed by the Powerpoint video export.


## How to install `pomalevi`

This is so far a crude and minimal solution, 
with no readthedocs documentation,
no release process, 
and no pip package. 

Requirements:
- `git` (for "installing" only)
- [ffmpeg](http://ffmpeg.org/) 4.3 (must be in the PATH)
- [Python 3](https://www.python.org/)
- I strongly recommend running pomalevi on 
  [WSL or WSL 2](https://docs.microsoft.com/en-us/windows/wsl/about) and
  below will assume you do so.  
  Running it directly on Windows is possible, but a bit more hassle
  (which you will have to figure out yourself).  
  The relevant differences are the lack of shebang lines
  (so you'll have to start it with `python -m pomalevi`
  instead of simply `pomalevy.py`), possible filename/backslash issues,
  and possible differences regarding `ffmpeg`; I have made no attempt
  (yet) to sort this out.
  Suitable pull requests are welcome.

To "install", 
- just clone the Github repo into a place of your choice:  
 `git clone https://github.com/prechelt/pomalevi.git`
- Put the path to `pomalevi.py` into your PATH or provide the
  path on each commandline (or make an alias).


## How to use `pomalevi`


### View demo.pptx (1 minute)

Go to the pomalevi install directoy tree,
open `demo/demo.pptx` with Powerpoint,
open "Powerpoint⟶Slide Show",
select "Play Narrations" and "Use Timings",
start the slide show.

You can now "File⟶Save as" this file,
select file format "Windows Media Video (*.wmv)",
and so create a `demo.wmv` file with you can use as the
`myslides.wmv` in the subsequent examples.


### Very basic use: Compression only

`pomalevi.py mydir/myslides.wmv`

The output is a directory `mydir/myslides/` with several files.
You can either use `mydir/myslides/index.html` 
to get the pomalevi player or
just the video itself: `mydir/myslides/v1.mp4`.


### Inserting stops: `-stop-at`

- In Powerpoint, choose a **unique graphic** or text string that will appear in your
  video to indicate to pomalevi where to insert a stop.
- For instance, I use "Insert⟶Icons⟶Business"
  pick the two people with the question mark (I have PowerPoint 2019),
  keep the default size, fill the icon with my highlight color (dark red),
  and put it in the lower left corner of my slide.
  (Any corner can be made to work easily, other places are possible if needed.)
- You could in principle also use the string "STOP!" or whatever other 
  fixed-and-unique visual element you like.
- Insert an **Entrance animation** for the logo at the appropriate moment,
  perhaps insert an Exit animation shortly thereafter.
  Only the entrance moment is relevant; it is the stop moment.  
  Note that the player is not capable of stopping at _exactly_ this moment;
  expect a tolerance of +0.25 seconds (0.5 seconds for Firefox).
- Export the video from PowerPoint.  
  Play it at original scale (that is, size 100%).  
  Stop it when the logo is visible.  
  Make a rectangular-area **screenshot** of only the logo.  
  Store it as PNG, e.g. `stoplogo.png`.
- Here is what the result looks like in my case:
  <img src="img/stoplogo.png" alt="Example pomalevi stop logo">
- pomalevi makes a pixel-by-pixel search for this image and expects
  a match of at least 80%, so beware of non-rectangular or transparent logos
  if the slide background is not always the same.
  See also section "Caveats" below.
- Now produce the video with pomalevi:  
  `pomalevi.py --stop-at ll:stoplogo.png mydir/myslides.wmv`  
  (`ll` stands for **"lower left"**)
- Searching for a stoplogo is a slooow process if done over the whole image.
  Therefore, pomalevi expects the logo to be in one of the four corners
  of the slide: one of `ul`, `ur`, `ll`, `lr` 
  in the `--stop-at` specification, meaning
  upper left, upper right, lower left, lower right, respectively.  
  It will find it there with a tolerance of up to half a logo width
  and half a logo height towards the middle of the video.
  If the logo hangs over the edge of the video even a bit, 
  it cannot be found reliably.  
  The part after the position specifier can be a pathname.
- In principle, you can also specify the search area by hand thusly:  
  `--stop-at x=900..1000,y=500..600:stoplogo.png`
  would look for the logo (specifically: the upper-left corner of the logo)
  in that region of the video (near the middle).  
  x=0,y=0 is the upper left corner.
- Unlike for basic use, this time the `v1.mp4` file is not helpful,
  because it knows nothing about the stops.  
  Instead, you need to use `mydir/myslides/index.html`, which calls
  the **pomalevi player** and feeds it the proper list of stop times.
- Like most pomalevi options, `--stop-at` has **friendly defaults**:
  - `--stop-at ll:stoplogo.png` will be assumed by default,
    but if `stoplogo.png` is not found, no stoplogo search will be performed.
  - The stoplogo will be searched for in several places:
    - `./stoplogo.png`, in the local directory
    - `mydir/stoplogo.png`, in the input file directory
    - `mydir/../stoplogo.png`, in the parent of the input file directory
    - `mydir/toc/stoplogo.png`, in the `toc` subdirectory of the input file 
      directory (see the description of `--toc` below).


### Splitting into parts: `--split-at`

The output of pomalevi appears a bit silly unless you let pomalevi 
split your video into several parts.

- Splitting works **much the same as stopping** (described above):  
  Decide on a logo (of course not the same as for stopping),  
  insert it in your presentation (say, in the lower right),  
  make a screenshot of it in the original size,  
  store it as `splitlogo.png` or so,  
  call pomalevi with it:  
  `pomalevi.py --split-at ll:splitlogo.png input.wmv outputdir`  
- Splitting creates a separate video file for each part, called
  `v1.mp4`, `v2.mp4`, etc.
- `mydir/myslides/index.html` provides navigation between those videos.
- The same **friendly defaults** apply as for `--stop-at`.


### Navigation with content description: `--toc`

All you get so far for navigation in the HTML file are generic section
titles "part 1", "part 2", etc. that are hyperlinks which load the respective
part of the video.
You can get a text to the right of each number that describes the
content of that video part and also get a meaningful title
for the HTML page by using the `--toc filename` option (table of contents):

The file given must be a UTF-8-encoded plain-text file
with a paragraph structure (as for instance MS Windows' `notepad` editor
can produce them).
Paragraphs are separated simply by an empty line.

The first paragraph (paragraph 0) provides the title of the 
`index.html` page.  
Subsequent paragraphs 1..N provide the content description for
video parts 1..N.

Example:
```
This is the title

This is the description of video part 1. It is a longer one that
takes multiple lines. Those lines will be rendered as a flowing
paragraph of text on the HTML page.

This is the description of video part 2.
```

Like most pomalevi options, `--toc` has **friendly defaults**:
- `--toc myslides-toc.txt` will be assumed by default,
  but if `myslides-toc.txt` is not found, the generic toc will be produced instead.
- The toc file will be searched for in several places:
  - `./myslides-toc.txt`, in the local directory
  - `mydir/myslides-toc.txt`, in the input file directory
  - `mydir/toc/stoplogo.png`, in the `toc` subdirectory of the input file 
     directory.

Taking all of the above together, the pomalevi call:  
`pomalevi.py --split-at lr:splitlogo.png --stop-at ll:stoplogo.png --toc input-contents.txt input.wmv outputdir`


### Overlapping Powerpoint export and pomalevi: waiting

- Powerpoint export takes a long time,
  pomalevi encoding also takes a long time.
  It would be nice if we could start pomalevi before Powerpoint has 
  finished exporting.  
  Consider it done!
- pomalevi will automatically wait until the given input file appears to 
  have been exported completely
  and only then start the actual pomalevi work.


### Output formats: MP4 vs. Webm

pomalevi currently produces `*.mp4` video files.

In the future, it will default to the more modern `*.webm`
(this is also what for instance YouTube uses)
and allow MP4 as an option.


## How it works

pomalevi uses ffmpeg's `find_rect` filter to find all frames
that contain the respective logo PNG content.
It uses the time information of these frames to drive the splitting
into parts and to feed the pomalevi player with the stop times
for each part.

`find_rect` cannot cope with scaling or rotation of the target image,
works only with a rectangular image, 
and it considers only a grayscale version of it with no alpha channel.

If you use a logo file `mylogo.png`, 
its grayscale derivative `mylogo.pgm` will appear
in the output directory during encoding (and then disappear again).


## Caveats

- On my machine, the MP4 files produced by PowerPoint's "Export" function
  are always broken: After a slide transition, when the new slide is already
  visible, the old one shortly reappears for varying lengths of time from
  a single frame to several tenths of a second.  
  So I use "Save as" with target format WMV instead.
  That's sort of silly (because WMV is the inferior format) but it works.
- Because of how it works (see above), the search for stop logo or split logo
  may fail if the background of the logo is not white.
  There must be enough contrast between the logo color(s) and the
  background color when converted to grayscale.
- Because of how it works (see above), the search for stop logo or split logo
  may fail if the logo has transparent parts and is placed onto other  
  material. The logo match is fuzzy, but expects at least an 80% match.
- Unless you place your logo _precisely_ in the corner, fine details in
  the logo will make the match worse. Prefer simple logos.

  
## TODO

Improvements waiting to be made:

- setuptools, static-ffmpeg, generate binary
- make demo.ppt
- command keywords `encode`, `compress`, `patch`.
- webm, `--mp4`
- smaller audio (by quality)
- `patch`
- `--ffmpeg` to submit encoding options
- `compress`
- highlight current video in toc
- make `pomalevi.css` mobile-ready
- `--favicon file`: Name of a 32x32 pixel PNG file to be used as the favicon.
- search for default `--toc` file `<basename>-toc.txt`  


## Versions

- 0.7, 2022-03-18
  - initial version, with most of the functionality:
    encode with splits and stops, basic CSS, TOC
- 0.8, 2022-04-28:
  - lots of small additions to functionality
  - obtain actual video resolution
  - modularized internal structure
  - friendly defaults for `--split-at`, `--stop-at`, `--toc`, `--out`.
