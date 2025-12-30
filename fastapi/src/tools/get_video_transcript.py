from youtube_transcript_api import YouTubeTranscriptApi

def get_video_transcript(video_id):
    try:
        # Fetching the transcript data
        transcript_list = YouTubeTranscriptApi.fetch(video_id)

        # Merging the snippets into a single block of text
        full_transcript = " ".join([entry['text'] for entry in transcript_list])

        return full_transcript

    except Exception as e:
        return f"An error occurred: {e}"

# Example: Using the video ID for a popular video
video_id = "qp0HIF3SfI4"
print(get_video_transcript(video_id))