# mp3fixup
Do cleanup operations on MP3 files.

*Use the Python version*

Currently does:
1) Runs `mp3val` to test and correct broken files
2) Runs `mp3gain` to set the gain (defaults to album, 89dB) on all files
3) Runs `mp3packer` to squish the file down as much as possible
