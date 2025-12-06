import re
import os

file_path = "downloader/backend/app.py"

# Read the entire file content
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define the start and end markers for the _process_single_entry function
start_marker = "    def _process_single_entry(entry_info):" # This line is at 8 spaces
end_marker = "            'is_playable': entry_info.get('is_playable', True) # For Instagram private/locked content" # This line is at 12 spaces

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.strip() == start_marker.strip():
        start_idx = i
    if start_idx != -1 and line.strip() == end_marker.strip():
        end_idx = i
        break

# The perfectly re-indented content for _process_single_entry
# This entire block will replace the original function.
re_indented_function_content = """    def _process_single_entry(entry_info):
        import sys
        import json
        print(\"--- HQMX DEBUG: RAW ENTRY INFO ---\", file=sys.stderr)
        print(json.dumps(entry_info, indent=2), file=sys.stderr)
        print(\"--- END RAW ENTRY INFO ---\", file=sys.stderr)
        video_formats = [extract_format_info(f) for f in entry_info.get('formats', []) if f and f.get('vcodec') != 'none']
        audio_formats = [extract_format_info(f) for f in entry_info.get('formats', []) if f and f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        gif_formats = [extract_format_info(f) for f in entry_info.get('formats', []) if f and f.get('ext') == 'gif'] # GIF-Check

        unique_video_formats = {f['format_id']: f for f in video_formats if f}.values()
        unique_audio_formats = {f['format_id']: f for f in audio_formats if f}.values()
        unique_gif_formats = {f['format_id']: f for f in gif_formats if f}.values() # GIF-Check

        # --- Thumbnail/Image Extraction Logic ---
        best_image_url = None
        best_image_width = None
        best_image_height = None

        thumbnails = entry_info.get('thumbnails')
        if isinstance(thumbnails, list) and thumbnails:
            # Sort by height (and then width) to find the best quality thumbnail
            best_thumbnail = max(thumbnails, key=lambda t: (t.get('height', 0) or 0, t.get('width', 0) or 0))
            best_image_url = best_thumbnail.get('url')
            best_image_width = best_thumbnail.get('width')
            best_image_height = best_thumbnail.get('height')
        elif entry_info.get('thumbnail'):
            best_image_url = entry_info.get('thumbnail')
        # FIX: Fallback for pure image entries (e.g., in Instagram carousels)
        # that don't have a 'thumbnail' field but a direct 'url' to the image.
        elif entry_info.get('url') and entry_info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
            best_image_url = entry_info.get('url')
            best_image_width = entry_info.get('width')
            best_image_height = entry_info.get('height')

        # If dimensions are still missing, try to infer them
        if best_image_url and (not best_image_width or not best_image_height):
            for f in entry_info.get('formats', []):
                if f and f.get('url') == best_image_url and f.get('width') and f.get('height'):
                    best_image_width = f.get('width')
                    best_image_height = f.get('height')
                    break

        # Determine media_type for the single entry
        media_type = 'unknown'
        print(f"DEBUG: Initial media_type: {media_type}", file=sys.stderr)

        # Apply image detection first for Instagram
        if entry_info.get('extractor_key') == 'Instagram':
            # Instagram carousel items of type 'GraphImage' or 'GraphSidecar' are always images
            if entry_info.get('__typename') in ['GraphImage', 'GraphSidecar']:
                media_type = 'image'
                unique_video_formats = {}
                unique_audio_formats = {}
            elif is_image_entry_helper(entry_info, best_image_url, unique_video_formats):
                media_type = 'image'
                # Clear video and audio formats if it's explicitly an image
                unique_video_formats = {}
                unique_audio_formats = {}
            elif entry_info.get('extractor_key') == 'Instagram' and entry_info.get('__typename') == 'GraphVideo':
                media_type = 'video'

        print(f"DEBUG: media_type before general fallback: {media_type}", file=sys.stderr)

        # --- General type detection (fallback) ---
        if media_type == 'unknown':
            if unique_gif_formats:
                media_type = 'gif'
            elif unique_video_formats:
                media_type = 'video'
            elif unique_audio_formats:
                media_type = 'audio'
            # Fallback to image if nothing else and an image URL is present
            elif best_image_url:
                media_type = 'image'

        # Final check for image-only types if still unknown
        if media_type == 'unknown' and not unique_video_formats and not unique_audio_formats and entry_info.get('ext') in ['jpg', 'jpeg', 'png', 'webp']:
            media_type = 'image'

        # Extract relevant image formats (highest quality image found)
        image_formats = []
        if media_type == 'image' and best_image_url:
            # Create a synthetic "image format" for the highest quality image
            image_formats.append({
                'format_id': 'original_image',
                'ext': best_image_url.split('.')[-1] if '.' in best_image_url else 'jpg', # Default to jpg if no ext
                'resolution': f"{best_image_width}x{best_image_height}" if best_image_width and best_image_height else 'N/A',
                'width': best_image_width,
                'height': best_image_height,
                'url': best_image_url,
                'filesize': entry_info.get('filesize') or entry_info.get('filesize_approx'),
                'note': 'Highest available image quality',
            })
        
        # Instagram/Pinterest specific: if it's an Instagram/Pinterest post and it's classified as video
        # but the only "video" is actually an image (e.g. 0 duration, or no actual vcodec)
        # Re-classify as image
        if entry_info.get('extractor_key') in ['Instagram', 'Pinterest'] and media_type == 'video':
            if entry_info.get('duration') == 0 or not any(f for f in unique_video_formats if f.get('vcodec') not in ['none', None]):
                media_type = 'image'
                unique_video_formats = {} # Clear video formats if re-classified

        return {
            'title': get_clean_title(entry_info),
            'url': entry_info.get('webpage_url') or entry_info.get('url'), # Use webpage_url for actual link if available
            'thumbnail': best_image_url,
            'thumbnail_width': best_image_width,
            'thumbnail_height': best_image_height,
            'duration': entry_info.get('duration'),
            'view_count': entry_info.get('view_count'),
            'media_type': media_type,
            'video_formats': sorted(list(unique_video_formats), key=lambda f: f.get('height') or 0, reverse=True),
            'audio_formats': sorted(list(unique_audio_formats), key=lambda f: f.get('abr') or 0, reverse=True),
            'gif_formats': sorted(list(unique_gif_formats), key=lambda f: f.get('height') or 0, reverse=True), # GIF-Check
            'image_formats': image_formats, # New field for images
            'is_playable': entry_info.get('is_playable', True) # For Instagram private/locked content
        }
"""


if start_idx != -1 and end_idx != -1:
    # Replace the old lines with the new, corrected block.
    # The splitlines() method inherently handles consistent line endings,
    # and we add a newline after each to maintain file structure.
    new_function_lines = [line + '\n' for line in re_indented_function_content.splitlines()]
    # Ensure the first line (def ...) is not double-indented
    # No, the `re_indented_function_content` is already correctly indented, no need to touch the first line.
    
    # Replace the old function definition with the new, re-indented content.
    new_lines = lines[:start_idx] + new_function_lines + lines[end_idx + 1:]
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Successfully replaced _process_single_entry in {file_path} with re-indented content.")
else:
    print(f"Error: Could not find the start or end markers for _process_single_entry in {file_path}.")
    print(f"Start Index: {start_idx}, End Index: {end_idx}")
    print("Please check the `start_marker` and `end_marker` or the file content manually.")

# --- Additional Debugging and Verification ---
with open(file_path, 'r', encoding='utf-8') as f:
    final_lines = f.readlines()

print("\n--- Modified File Content (relevant section) ---")
# Print a wider context around the modification for verification
# Let's target the start of the function and some lines after for context.
context_start_line = start_idx
for i in range(max(0, context_start_line - 5), min(len(final_lines), context_start_line + 10 + len(re_indented_function_content.splitlines()))):
    print(f"{i+1:4d} {final_lines[i].rstrip()}")
print("---------------------------------------------")
