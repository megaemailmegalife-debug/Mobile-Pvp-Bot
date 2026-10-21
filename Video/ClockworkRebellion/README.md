# Clockwork Rebellion

A complete 2:40 instrumental music video, 1920 x 1080, 24 fps, stereo sound.
Original procedural 3D motion graphics: 27 camera shots, articulated dancing robots, moving mechanical architecture, a floating interlude and a twelve-dancer finale.
No filmed footage, stock animation, downloaded models or third-party sound recordings.

## Music and reuse
Composition: Edvard Grieg, "In the Hall of the Mountain King", Peer Gynt Suite No. 1, Op. 46.
Grieg lived 1843–1907. The composition is public domain in the United States and standard life-plus-70 jurisdictions.

Public-domain source verification: University of Rochester / Sibley Music Library, 1899 score:
https://urresearch.rochester.edu/institutionalPublicationPublicView.action?institutionalItemVersionId=17123

The arrangement and recording were generated for this video by audio.py. Every instrument and drum sound is synthesized mathematically. No modern commercial recording or audio sample is used. There are no vocals.

The original generated animation, scene models, choreography, music arrangement and synthesized recording are supplied for unrestricted reuse. To the extent copyright or related rights exist in this generated project material and can be waived, that material is dedicated under CC0 1.0:
https://creativecommons.org/publicdomain/zero/1.0/

The underlying historical composition is public domain independently of the dedication. Software dependencies retain their own licenses. The title-card font is DejaVu Sans under the DejaVu font license.

## Story
A sleeping mechanical city discovers its rhythm. A small coral-and-ivory robot releases a luminous pulse, invites other dancers, and turns clockwork into choreography. The dancers float inside a kinetic mobile before returning for a finale where the great clock blossoms.

## Source and reproduction
Python 3.11, NumPy, SciPy, Pillow, ModernGL, FFmpeg and EGL/OpenGL 3.3.
The workflow renders four sequential chunks on isolated runners, then joins them with the original soundtrack.

python audio.py
python render.py --width 1920 --height 1080 --fps 24
