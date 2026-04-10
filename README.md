# rope

> [!CAUTION]
> using this tool is literally self-harm. you will not like the numbers. you will run it again tomorrow anyway.

face analyzer for your selfie collection. uses [deepface](https://github.com/serengil/deepface) (this one is rough) to tell you how various attributes (gender, age, emotions) changed over time

## what it does

- scans every image in a directory
- detects faces and tells you age, gender, race, emotion
- reads EXIF dates and groups results into time periods
- shows you a trend table of how your averages shifted

## usage

you'll need nix, idk how to run it anywhere else
and you'll need to download all your photos from google photos or something :D

```sh
nix run github:surfaceflinger/rope -- /path/to/your/selfies

# customize period length (default 4 months)
nix run github:surfaceflinger/rope -- -m 6 /path/to/selfies
```

## faq

**q: why is it called rope**

a: you'll understand after running it

**q: the age estimate is wrong**

a: maybe
