from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/formats", methods=["POST"])
def get_formats():
    data = request.json
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = []

            for f in info.get("formats", []):
                if f.get("ext") in ["mp4", "webm"] and f.get("height"):  # Video formats
                    formats.append({
                        "format_id": f["format_id"],
                        "ext": f["ext"],
                        "resolution": f"{f['height']}p",
                        "fps": f.get("fps", "N/A"),
                        "filesize": f.get("filesize", 0),
                    })
                elif f.get("vcodec") == "none" and f.get("acodec") != "none":  # Audio formats
                    formats.append({
                        "format_id": f["format_id"],
                        "ext": f["ext"],
                        "audio_bitrate": f.get("abr", "Unknown"),
                        "filesize": f.get("filesize", 0),
                    })

        return jsonify({"formats": formats})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json
    video_url = data.get("url")
    format_id = data.get("format")

    if not video_url or not format_id:
        return jsonify({"error": "Missing URL or format"}), 400

    try:
        cookies_path = "cookies.txt"  # Ensure this file exists in your project directory

        ydl_opts = {
            "format": format_id,  # Use the selected format ID
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "cookies": cookies_path,  # Pass cookies to bypass login restrictions
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)

        return jsonify({"message": "Download complete", "file_path": file_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get-file", methods=["GET"])
def get_file():
    file_path = request.args.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
