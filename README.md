# pomalevi

PowerPoint-based maintainable lecture videos command-line tool

Simple and effective.

If you are afraid of using the command-line, this is not for you.


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
- it produces an HTML page with table of content hyperlinks for these
  parts based on a very simple text file containing parts descriptions
- it provides a simple HTML player that will stop the video
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

pomalevi is tested on Windows, but should also work on WSL or Linux proper.
It is a command-line application, so you need to work in cmd.exe or 
Powershell.

- Install a recent version of Python (3.8 or higher) from
  https://python.org.  
  Commands `python` and `pip` must end up on your `PATH`.
- Start cmd.exe or powershell and perform `pip install pomalevi`
- That's all!  
  You should now be able to call `pomalevi`.

Caveats:
- The above should work on personal computers.  
  If you have a pre-installed version of Python but are not allowed to use
 `pip` as shown (you should be!),
  - use `pip install --user pomalevi` instead to install to your
    personal directory instead
  - use `pip show pomalevi` to see (in the "Location:" entry) 
    where it ended up, e.g.
    `c:\Users\<name>\AppData\Roaming\Python\Python310\site-packages`
  - put the neighboring `Scripts` directory in your `Path`, e.g.
    `c:\Users\<name>\AppData\Roaming\Python\Scripts`.  
    (To modify `Path`, use the Windows key, search for "environment"`,
    and call "Edit environment variables for your account" (not "for system").
    If your Windows is not running in English, the name will be different,
    but the English search term should still work.)
  Pomalevi should now work like after the original procedure.  
  Alternatively, you could perform an additional install of Python
  in "for me only" fashion and use the pip of that.
- The above installation procedure is a shortcut: If used, pomalevi
  could _in principle_ interfere with other Python packages installed on your
  machine (although that is unlikely to be a problem).  
  A cleaner way would use `pipx` instead of `pip`, which installs a
  package in an isolated environment.
  To do that, 
  - first install `pipx` by `pip install pipx`
  - then install pomalevi by `pipx install pomalevi`
  - and then put the path displayed by `pipx` into your `PATH`


## How to use `pomalevi`


### View demo.pptx (1 minute)

Find the pomalevi install directory tree in the
directory ending in `site-packages` which is shown when you execute 
`python -c "import sys; print(sys.path)"`.

From the pomalevi install directory tree,
copy `ppt/demo.pptx` to any of your own directories.  
Open the copy with Powerpoint,  
choose "Powerpoint⟶Slide Show",  
check the boxes for "Play Narrations" and "Use Timings",  
start the slide show.  
View it, end it. Imagine this was your own presentation which you want
to publish as several videos in pomalevi style.

To do that, "File⟶Save as" this file,
select file format "Windows Media Video (*.wmv)",
and save it as `myslides.wmv`.
This file you can use as the `myslides.wmv` in the subsequent examples.


### Very basic use: Compression only

`pomalevi mydir/myslides.wmv`

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
  if the slide background behind it will not always be the same.
  See also section "Caveats" below.
- Now produce the video with pomalevi:  
  `pomalevi --stop-at ll:stoplogo.png mydir/myslides.wmv`  
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
  Decide on a logo (of course not the same one as for stopping),  
  insert it in your presentation (preferably again in the lower right),  
  make a screenshot of it in the original size,  
  store it as (preferably) `splitlogo.png`, and  
  call pomalevi with it:    
  `pomalevi --split-at ll:splitlogo.png input.wmv`  
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
with a paragraph structure. 
Use any text editor (for instance MS Windows' `notepad`)
to produce them.
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

This is the description of the second video part, number 2.
```

Like most pomalevi options, `--toc` has **friendly defaults**:
- `--toc myslides-toc.txt` will be assumed by default,
  but if `myslides-toc.txt` is not found, the generic toc will be produced instead.
- The toc file will be searched for in several places:
  - `./myslides-toc.txt`, in the local directory
  - `mydir/myslides-toc.txt`, in the input file directory
  - `mydir/toc/stoplogo.png`, in the `toc` subdirectory of the input file 
     directory.


### Output directory: `--out`

So far, we have always used the **friendly default** to tell
pomalevi where we want the output to end up:
If the input file is `mydir/myslides.wmv`, the output will go to
`mydir/myslides/*`.

If you don't want this, specifiy a target directory with `--out`:  
`pomalevi --out outputdir mydir/myslides.wmv`.


### Friendly defaults rough summary

Taking all of the above together, the explicit pomalevi call could be:  
`pomalevi --split-at ll:splitlogo.png --stop-at ll:stoplogo.png --toc mydir/myslides-toc.txt --out mydir/myslides mydir/myslides.wmv`  
but the following is equivalent, courtesy of the defaults:  
`pomalevi mydir/myslides.wmv`


### Overlapping Powerpoint export and pomalevi: waiting

- Powerpoint export takes a long time,
  pomalevi encoding also takes a long time.
  It would be nice if we could start pomalevi before Powerpoint has 
  finished exporting.  
  Consider it done!
- pomalevi will automatically wait until the given input file appears to 
  have been exported completely
  and only then start the actual pomalevi work.


### Encoding type and quality: `--format`

pomalevi can produce either 
`*.mp4` video files 
(encoded with H.264 video and AAC audio) or 
`*.webm` video files
(encoded with VP8 video and Opus audio).

`webm` encoding currently uses rather naive settings and is not recommended.

`mp4` encoding is available with four different sets of settings, called
q1 to q4, that produce different quality levels and file sizes.  
q1 creates the smallest files with the lowest audio and video quality,  
q4 creates the largest files with the highest quality.

These are selected using  
`--format mp4q1`  
`--format mp4q2`  
`--format mp4q3`  
`--format mp4q4`  
`--format webm`

`mp4q3` is the default.


## How pomalevi works internally

pomalevi uses [ffmpeg](https://ffmpeg.org)'s `find_rect` filter 
to find all frames that contain the respective logo PNG content.
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
  That's sort of silly (because WMV is the inferior format) but at least it works.
- Because of how pomalevi works (see above), the search for stop logo or split logo
  may fail if the background of the logo is colored.
  There must be enough contrast between the logo color(s) and the
  background color when converted to grayscale.
- Because of how it works (see above), the search for stop logo or split logo
  may fail if the logo has transparent parts and is placed onto other  
  material. The logo match is fuzzy, but expects at least an 80% match.
- Unless you place your logo _precisely_ in the corner, fine details in
  the logo will make the match worse. Prefer simple logos.

  
## TODO

Improvements waiting to be made:

- make demo.ppt
- command keywords `encode`, `compress`, `patch`, `get-logos`, `get-demo`.
- `--ffmpeg-a`, `--ffmpeg-v` to submit encoding options
- highlight current video in toc
- make `pomalevi.css` mobile-ready
- `--favicon file`: Name of a 32x32 pixel PNG file to be used as the favicon.


## Versions

- 0.7, 2022-03-18
  - initial version, with most of the functionality:
    encode with splits and stops, basic CSS, TOC
- 0.8, 2022-04-28:
  - lots of small additions to functionality
  - obtain actual video resolution
  - modularized internal structure
  - friendly defaults for `--split-at`, `--stop-at`, `--toc`, `--out`.
- 0.9, 2022-04-29:
  - use `static-ffmpeg` Python package, no longer the system's ffmpeg
  - use Poetry build system and produce `pomalevi.exe`
- 1.0, 2022-05-06
  - add `--format`
  - add `ppt/demo.pptx`