FFMPEGFILE=ffmpeg.exe
if ! [ -f "$FFMPEGFILE" ]; then
  curl -L https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip -O
  unzip ffmpeg-release-essentials.zip -d ffmpeg
  cd ffmpeg && cd $(ls -d */|head -n 1) && cd bin
  mv ffmpeg.exe ../ && cd ..
  mv ffmpeg.exe ../ && cd ..
  mv ffmpeg.exe ../ && cd ..
  rm ffmpeg-release-essentials.zip
  rm -r ffmpeg
fi

mkdir -p downloads
mkdir -p logs

if [ -x "$(command -v pip3)" ]; then
  pip3 install -r requirements.txt
fi