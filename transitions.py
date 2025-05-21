import numpy as np
from moviepy import VideoClip, CompositeVideoClip, vfx

def fade(clip1, clip2, duration=1.0):
    """Simple fade transition between two clips."""
    return clip1.crossfadeout(duration).set_duration(clip1.duration) \
           .crossfadein(clip2, duration)

def dissolve(clip1, clip2, duration=1.0):
    """Dissolve transition (another name for crossfade)."""
    clip1 = clip1.set_duration(clip1.duration)
    clip2 = clip2.set_start(clip1.duration - duration)
    return CompositeVideoClip([clip1, clip2.crossfadein(duration)])

def wipe_left(clip1, clip2, duration=1.0):
    """Wipe from right to left transition."""
    def make_frame(t):
        if t < duration:
            w = clip1.w * (1 - t/duration)
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame2.copy()
            result[:, :int(w)] = frame1[:, :int(w)]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def wipe_right(clip1, clip2, duration=1.0):
    """Wipe from left to right transition."""
    def make_frame(t):
        if t < duration:
            w = clip1.w * (t/duration)
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame1.copy()
            result[:, int(clip1.w - w):] = frame2[:, int(clip1.w - w):]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def wipe_up(clip1, clip2, duration=1.0):
    """Wipe from bottom to top transition."""
    def make_frame(t):
        if t < duration:
            h = clip1.h * (1 - t/duration)
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame2.copy()
            result[:int(h), :] = frame1[:int(h), :]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def wipe_down(clip1, clip2, duration=1.0):
    """Wipe from top to bottom transition."""
    def make_frame(t):
        if t < duration:
            h = clip1.h * (t/duration)
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame1.copy()
            result[int(clip1.h - h):, :] = frame2[int(clip1.h - h):, :]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def slide_left(clip1, clip2, duration=1.0):
    """Slide from right to left transition."""
    def make_frame(t):
        if t < duration:
            offset = int(clip1.w * (t/duration))
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame1.copy()
            result[:, :clip1.w-offset] = frame1[:, offset:]
            result[:, clip1.w-offset:] = frame2[:, :offset]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def slide_right(clip1, clip2, duration=1.0):
    """Slide from left to right transition."""
    def make_frame(t):
        if t < duration:
            offset = int(clip1.w * (t/duration))
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            result = frame1.copy()
            result[:, offset:] = frame1[:, :clip1.w-offset]
            result[:, :offset] = frame2[:, clip1.w-offset:]
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def zoom_in(clip1, clip2, duration=1.0):
    """Zoom in transition."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            zoom_factor = 1 + progress
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Apply zoom to frame1
            zoomed1 = vfx.resize(VideoClip(lambda t: frame1), zoom_factor).get_frame(0)
            
            # Calculate crop to get center
            h, w = frame1.shape[:2]
            crop_h, crop_w = int(h * (1-1/zoom_factor)/2), int(w * (1-1/zoom_factor)/2)
            zoomed1_cropped = zoomed1[crop_h:crop_h+h, crop_w:crop_w+w]
            
            # Blend between zoomed clip1 and clip2
            alpha = progress
            return (1-alpha) * zoomed1_cropped + alpha * frame2
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def zoom_out(clip1, clip2, duration=1.0):
    """Zoom out transition."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            zoom_factor = 1 + (1 - progress)
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Apply zoom to frame2
            zoomed2 = vfx.resize(VideoClip(lambda t: frame2), zoom_factor).get_frame(0)
            
            # Calculate crop to get center
            h, w = frame2.shape[:2]
            crop_h, crop_w = int(h * (1-1/zoom_factor)/2), int(w * (1-1/zoom_factor)/2)
            zoomed2_cropped = zoomed2[crop_h:crop_h+h, crop_w:crop_w+w]
            
            # Blend between clip1 and zoomed clip2
            alpha = progress
            return (1-alpha) * frame1 + alpha * zoomed2_cropped
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def blur_transition(clip1, clip2, duration=1.0, blur_intensity=20):
    """Blur transition between two clips."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Calculate blur factor based on progress (most blur in the middle)
            blur_factor = blur_intensity * (1 - abs(2 * progress - 1))
            
            # Apply blur to both frames
            blurred1 = vfx.gaussian_blur(VideoClip(lambda t: frame1), blur_factor).get_frame(0)
            blurred2 = vfx.gaussian_blur(VideoClip(lambda t: frame2), blur_factor).get_frame(0)
            
            # Crossfade between blurred frames
            return (1-progress) * blurred1 + progress * blurred2
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def whip_pan(clip1, clip2, duration=0.5):
    """Fast whip pan transition with motion blur."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            
            # More motion blur in the middle of the transition
            blur_factor = 30 * (1 - abs(2 * progress - 1)) 
            
            if progress < 0.5:
                # First half: blur the first clip increasingly
                frame = clip1.get_frame(clip1.duration - duration + t)
                return vfx.gaussian_blur(VideoClip(lambda t: frame), blur_factor).get_frame(0)
            else:
                # Second half: blur the second clip decreasingly
                frame = clip2.get_frame(t)
                return vfx.gaussian_blur(VideoClip(lambda t: frame), blur_factor).get_frame(0)
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def rotate_transition(clip1, clip2, duration=1.0, angle=360):
    """Rotating transition between clips."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            current_angle = progress * angle
            
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Rotate and scale clip1
            clip1_rotated = vfx.rotate(VideoClip(lambda t: frame1), current_angle, expand=False).get_frame(0)
            
            # Scale down clip1 as it rotates
            scale_factor = 1 - 0.5 * progress
            if scale_factor > 0:
                clip1_scaled = vfx.resize(VideoClip(lambda t: clip1_rotated), scale_factor).get_frame(0)
                
                # Center the scaled clip
                h, w = frame1.shape[:2]
                sh, sw = clip1_scaled.shape[:2]
                y_offset = max(0, (h - sh) // 2)
                x_offset = max(0, (w - sw) // 2)
                
                result = frame2.copy()
                mask = (1 - progress) ** 0.5  # Fade out mask
                
                # Blend the rotated clip1 onto clip2
                if y_offset + sh <= h and x_offset + sw <= w:
                    result[y_offset:y_offset+sh, x_offset:x_offset+sw] = \
                        mask * clip1_scaled + (1-mask) * result[y_offset:y_offset+sh, x_offset:x_offset+sw]
                
                return result
            else:
                return frame2
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def door_wipe(clip1, clip2, duration=1.0, from_center=True):
    """Door wipe transition (opening from center or closing to center)."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            result = frame1.copy()
            h, w = frame1.shape[:2]
            
            if from_center:
                # Opening from center
                mid_w = w // 2
                door_w = int(mid_w * progress)
                
                # Left door
                result[:, mid_w-door_w:mid_w] = frame2[:, mid_w-door_w:mid_w]
                # Right door
                result[:, mid_w:mid_w+door_w] = frame2[:, mid_w:mid_w+door_w]
            else:
                # Closing to center
                door_w = int(w * (1 - progress) / 2)
                
                # Keep only the "doors" from clip1
                result[:, :door_w] = frame1[:, :door_w]
                result[:, w-door_w:] = frame1[:, w-door_w:]
                
                # The rest is from clip2
                result[:, door_w:w-door_w] = frame2[:, door_w:w-door_w]
                
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def circle_wipe(clip1, clip2, duration=1.0, from_center=True):
    """Circle wipe transition (expanding or contracting circle)."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            center_y, center_x = h // 2, w // 2
            
            # Create distance matrix from center
            y, x = np.ogrid[:h, :w]
            dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            
            # Maximum possible distance (from center to corner)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            
            if from_center:
                # Expanding circle
                radius = max_dist * progress
                mask = dist_from_center < radius
            else:
                # Contracting circle
                radius = max_dist * (1 - progress)
                mask = dist_from_center > radius
            
            result = frame1.copy()
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def diamond_wipe(clip1, clip2, duration=1.0, from_center=True):
    """Diamond-shaped wipe transition."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            center_y, center_x = h // 2, w // 2
            
            # Create Manhattan distance matrix from center
            y, x = np.ogrid[:h, :w]
            manhattan_dist = np.abs(x - center_x) + np.abs(y - center_y)
            
            # Maximum possible Manhattan distance
            max_dist = center_x + center_y
            
            if from_center:
                # Expanding diamond
                threshold = max_dist * progress
                mask = manhattan_dist < threshold
            else:
                # Contracting diamond
                threshold = max_dist * (1 - progress)
                mask = manhattan_dist > threshold
            
            result = frame1.copy()
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def clock_wipe(clip1, clip2, duration=1.0, clockwise=True):
    """Clock wipe transition."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            center_y, center_x = h // 2, w // 2
            
            # Create angle matrix
            y, x = np.ogrid[:h, :w]
            angles = np.arctan2(y - center_y, x - center_x)
            
            # Convert angles to range [0, 2π]
            angles = (angles + 2 * np.pi) % (2 * np.pi)
            
            # Clockwise starts from 0 radians, counter-clockwise from π
            start_angle = 0 if clockwise else np.pi
            current_angle = progress * 2 * np.pi
            
            if clockwise:
                mask = angles <= current_angle
            else:
                mask = angles >= (2 * np.pi - current_angle)
            
            result = frame1.copy()
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def split_screen(clip1, clip2, duration=1.0, direction="horizontal"):
    """Split screen transition (horizontal or vertical)."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            result = frame1.copy()
            
            if direction == "horizontal":
                # The split moves from left to right
                split_x = int(w * progress)
                result[:, :split_x] = frame2[:, :split_x]
            else:  # vertical
                # The split moves from top to bottom
                split_y = int(h * progress)
                result[:split_y, :] = frame2[:split_y, :]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def venetian_blinds(clip1, clip2, duration=1.0, blinds=10, direction="horizontal"):
    """Venetian blinds transition effect."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            result = frame1.copy()
            
            if direction == "horizontal":
                # Horizontal blinds
                blind_height = h // blinds
                for i in range(blinds):
                    y_start = i * blind_height
                    y_end = min((i + 1) * blind_height, h)
                    
                    # Calculate width of the blind that should show clip2
                    blind_width = int(w * progress)
                    result[y_start:y_end, :blind_width] = frame2[y_start:y_end, :blind_width]
            else:
                # Vertical blinds
                blind_width = w // blinds
                for i in range(blinds):
                    x_start = i * blind_width
                    x_end = min((i + 1) * blind_width, w)
                    
                    # Calculate height of the blind that should show clip2
                    blind_height = int(h * progress)
                    result[:blind_height, x_start:x_end] = frame2[:blind_height, x_start:x_end]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def checkerboard(clip1, clip2, duration=1.0, squares=8):
    """Checkerboard transition effect."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            result = frame1.copy()
            
            # Size of each square
            square_h = h // squares
            square_w = w // squares
            
            # Create an evenly sized grid if possible
            rows = h // square_h
            cols = w // square_w
            
            # The number of squares to fill (progress determines how many)
            fill_squares = int(progress * rows * cols)
            
            # Fill squares in a checkerboard pattern
            count = 0
            for r in range(rows):
                for c in range(cols):
                    if count < fill_squares:
                        y_start = r * square_h
                        y_end = min((r + 1) * square_h, h)
                        x_start = c * square_w
                        x_end = min((c + 1) * square_w, w)
                        
                        # Only fill if it's a checkerboard pattern
                        if (r + c) % 2 == 0:
                            result[y_start:y_end, x_start:x_end] = frame2[y_start:y_end, x_start:x_end]
                            count += 1
            
            # Fill the remaining checkerboard squares if needed
            if count < fill_squares:
                remaining = fill_squares - count
                count = 0
                for r in range(rows):
                    for c in range(cols):
                        if count < remaining:
                            y_start = r * square_h
                            y_end = min((r + 1) * square_h, h)
                            x_start = c * square_w
                            x_end = min((c + 1) * square_w, w)
                            
                            # Fill the odd squares now
                            if (r + c) % 2 == 1:
                                result[y_start:y_end, x_start:x_end] = frame2[y_start:y_end, x_start:x_end]
                                count += 1
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def push(clip1, clip2, duration=1.0, direction="left"):
    """Push transition where one clip pushes the other off screen."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            result = np.zeros_like(frame1)
            
            if direction == "left":
                # clip2 pushes clip1 to the left
                offset = int(w * progress)
                if offset < w:
                    result[:, :w-offset] = frame1[:, offset:]
                if offset > 0:
                    result[:, w-offset:] = frame2[:, :offset]
            
            elif direction == "right":
                # clip2 pushes clip1 to the right
                offset = int(w * progress)
                if offset < w:
                    result[:, offset:] = frame1[:, :w-offset]
                if offset > 0:
                    result[:, :offset] = frame2[:, w-offset:]
            
            elif direction == "up":
                # clip2 pushes clip1 up
                offset = int(h * progress)
                if offset < h:
                    result[:h-offset, :] = frame1[offset:, :]
                if offset > 0:
                    result[h-offset:, :] = frame2[:offset, :]
            
            elif direction == "down":
                # clip2 pushes clip1 down
                offset = int(h * progress)
                if offset < h:
                    result[offset:, :] = frame1[:h-offset, :]
                if offset > 0:
                    result[:offset, :] = frame2[h-offset:, :]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def luma_wipe(clip1, clip2, duration=1.0, luma_map=None):
    """Luma wipe transition using a grayscale image as a map."""
    import scipy.ndimage as ndi
    
    if luma_map is None:
        # Create a radial gradient if no luma_map is provided
        h, w = clip1.h, clip1.w
        y, x = np.ogrid[:h, :w]
        center_y, center_x = h // 2, w // 2
        luma_map = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        luma_map = luma_map / luma_map.max()
    else:
        # Ensure luma_map is normalized between 0 and 1
        luma_map = (luma_map - luma_map.min()) / (luma_map.max() - luma_map.min())
    
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Use luma_map to transition between clips
            # Values below threshold will show frame2, values above will show frame1
            threshold = progress
            mask = luma_map < threshold
            
            result = frame1.copy()
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def flip_transition(clip1, clip2, duration=1.0, axis="x"):
    """3D flip transition around x or y axis."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            
            # Get frames
            if progress < 0.5:
                # First half: show clip1 flipping away
                angle = progress * 180
                frame = clip1.get_frame(clip1.duration - duration + t)
            else:
                # Second half: show clip2 flipping in
                angle = (progress - 0.5) * 180
                frame = clip2.get_frame(t)
            
            h, w = frame.shape[:2]
            
            # Apply perspective transformation based on angle
            if axis == "y":
                # Flip around y-axis (horizontal flip)
                # As angle approaches 90, the width approaches 0
                scale = abs(np.cos(np.radians(angle)))
                if scale < 0.01: scale = 0.01  # Avoid division by zero
                
                # Scale width
                new_w = int(w * scale)
                
                if new_w > 0:
                    # Apply horizontal squeeze
                    offset = (w - new_w) // 2
                    resized = np.zeros_like(frame)
                    
                    if progress < 0.5:
                        # Flip direction depends on which half we're in
                        if new_w > 0:
                            for i in range(new_w):
                                resized[:, offset+i] = frame[:, int(i/scale)]
                    else:
                        if new_w > 0:
                            for i in range(new_w):
                                resized[:, offset+i] = frame[:, w-1-int(i/scale)]
                    
                    return resized
                else:
                    # At the exact midpoint, return a blank frame
                    return np.zeros_like(frame)
            else:
                # Flip around x-axis (vertical flip)
                # As angle approaches 90, the height approaches 0
                scale = abs(np.cos(np.radians(angle)))
                if scale < 0.01: scale = 0.01
                
                # Scale height
                new_h = int(h * scale)
                
                if new_h > 0:
                    # Apply vertical squeeze
                    offset = (h - new_h) // 2
                    resized = np.zeros_like(frame)
                    
                    if progress < 0.5:
                        # Flip direction depends on which half we're in
                        if new_h > 0:
                            for i in range(new_h):
                                resized[offset+i, :] = frame[int(i/scale), :]
                    else:
                        if new_h > 0:
                            for i in range(new_h):
                                resized[offset+i, :] = frame[h-1-int(i/scale), :]
                    
                    return resized
                else:
                    # At the exact midpoint, return a blank frame
                    return np.zeros_like(frame)
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def pixel_dissolve(clip1, clip2, duration=1.0, seed=None):
    """Pixel dissolve transition (random pixels change from clip1 to clip2)."""
    if seed is not None:
        np.random.seed(seed)
    
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            
            # Create random pixel order once (reused for all frames)
            if not hasattr(make_frame, 'pixel_order'):
                make_frame.pixel_order = np.random.permutation(h * w).reshape(h, w)
            
            # Normalize the order to 0-1 range
            normalized_order = make_frame.pixel_order / (h * w)
            
            # Create mask based on current progress
            mask = normalized_order < progress
            
            result = frame1.copy()
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def burn_transition(clip1, clip2, duration=1.0):
    """Burn-like transition effect."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Create "burn" effect by darkening and adding orange/red tint
            # Then gradually reveal clip2
            
            # Create a darkened version of clip1
            darkened = frame1.copy().astype(float) * (1 - 0.7 * progress)
            
            # Add orange/red tint to the darkening areas
            if len(frame1.shape) == 3:  # Color images
                # Increase red channel, slightly increase green, reduce blue
                darkened[:,:,0] = np.minimum(255, darkened[:,:,0] + 40 * progress)  # Red
                darkened[:,:,2] = np.maximum(0, darkened[:,:,2] - 50 * progress)    # Blue
            
            # Create random-ish mask for transition progression
            h, w = frame1.shape[:2]
            if not hasattr(make_frame, 'noise'):
                # Create a noise pattern once
                make_frame.noise = np.random.rand(h, w)
            
            # Create a gradient from bottom to top to make it burn upward
            y_gradient = np.linspace(0, 1, h)[:, np.newaxis] * np.ones((h, w))
            noise_with_gradient = make_frame.noise + y_gradient
            
            # Normalize
            noise_with_gradient = (noise_with_gradient - noise_with_gradient.min()) / (noise_with_gradient.max() - noise_with_gradient.min())
            
            # Create mask based on progress
            mask = noise_with_gradient < progress
            
            # Fill in clip2 where the mask is True
            result = darkened.astype(np.uint8)
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    result[:,:,i][mask] = frame2[:,:,i][mask]
            else:  # Grayscale
                result[mask] = frame2[mask]
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def ripple_transition(clip1, clip2, duration=1.0, amplitude=10, frequency=5):
    """Water ripple transition effect."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            y, x = np.mgrid[:h, :w]
            
            # Calculate center for the ripple
            center_y, center_x = h // 2, w // 2
            
            # Calculate distance from center for each pixel
            dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            
            # Calculate ripple effect
            # The ripple expands outward, so we subtract progress from normalized distance
            # Multiply by frequency to get multiple ripple waves
            ripple = np.sin((dist / np.max(dist) - progress) * 2 * np.pi * frequency)
            
            # Scale ripple effect and make it decrease with progress
            ripple = ripple * amplitude * (1 - progress)
            
            # Apply displacement to create ripple
            y_ripple = y + ripple * (y - center_y) / (dist + 1)
            x_ripple = x + ripple * (x - center_x) / (dist + 1)
            
            # Ensure coordinates are within bounds
            y_ripple = np.clip(y_ripple, 0, h-1).astype(int)
            x_ripple = np.clip(x_ripple, 0, w-1).astype(int)
            
            # Apply ripple distortion to frame1
            rippled = np.zeros_like(frame1)
            if len(frame1.shape) == 3:  # Color images
                for i in range(3):  # Apply to each channel
                    rippled[:,:,i] = frame1[y_ripple, x_ripple, i]
            else:  # Grayscale
                rippled = frame1[y_ripple, x_ripple]
            
            # Crossfade between rippled frame1 and frame2
            result = ((1 - progress) * rippled + progress * frame2).astype(np.uint8)
            
            return result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def flash_transition(clip1, clip2, duration=1.0, flash_intensity=1.5, flash_duration=0.2):
    """Flash transition - a bright flash occurs between clips."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            # Determine flash intensity at current time
            # Flash should peak in the middle of the transition
            if flash_duration > 0:
                flash_midpoint = 0.5
                flash_start = flash_midpoint - flash_duration/2
                flash_end = flash_midpoint + flash_duration/2
                
                if progress < flash_start:
                    # Before flash: show clip1
                    flash_factor = 0
                    alpha = 1
                elif progress < flash_midpoint:
                    # Ramping up flash
                    flash_factor = (progress - flash_start) / (flash_midpoint - flash_start) * flash_intensity
                    alpha = 1 - (progress - flash_start) / (flash_midpoint - flash_start)
                elif progress < flash_end:
                    # Ramping down flash
                    flash_factor = (flash_end - progress) / (flash_end - flash_midpoint) * flash_intensity
                    alpha = 0
                else:
                    # After flash: show clip2
                    flash_factor = 0
                    alpha = 0
            else:
                # No flash duration specified, simple crossfade with flash at midpoint
                flash_factor = (1 - abs(progress - 0.5) * 2) * flash_intensity
                alpha = 1 - progress
            
            # Apply flash and blend frames
            if flash_factor > 0:
                # Create white flash
                flash = np.ones_like(frame1) * 255
                # Blend with current frame
                blend = frame1 if alpha > 0.5 else frame2
                flashed = blend * (1 - flash_factor) + flash * flash_factor
                flashed = np.clip(flashed, 0, 255).astype(np.uint8)
            else:
                # No flash, just blend between clips
                flashed = frame1 if alpha == 1 else frame2 if alpha == 0 else (frame1 * alpha + frame2 * (1 - alpha))
            
            return flashed
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

def glitch_transition(clip1, clip2, duration=1.0, intensity=0.1, n_glitches=10):
    """Glitch effect transition between clips."""
    def make_frame(t):
        if t < duration:
            progress = t / duration
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)
            
            h, w = frame1.shape[:2]
            result = frame1.copy() if progress < 0.5 else frame2.copy()
            
            # Apply glitch effects
            # Intensity of glitches peaks in the middle of the transition
            current_intensity = intensity * (1 - abs(progress - 0.5) * 2)
            
            # Skip glitch if intensity is too low
            if current_intensity < 0.01:
                return (frame1 * (1 - progress) + frame2 * progress).astype(np.uint8)
            
            # Generate random glitches
            for _ in range(n_glitches):
                # Random glitch type
                glitch_type = np.random.randint(0, 4)
                
                if glitch_type == 0:
                    # Horizontal line offset
                    y_start = np.random.randint(0, h)
                    height = int(max(1, h * 0.01 * current_intensity * np.random.rand()))
                    y_end = min(y_start + height, h)
                    offset = int(w * current_intensity * np.random.uniform(-1, 1))
                    
                    if offset != 0:
                        if len(result.shape) == 3:  # Color
                            if offset > 0:
                                result[y_start:y_end, offset:] = result[y_start:y_end, :-offset]
                            else:
                                result[y_start:y_end, :offset] = result[y_start:y_end, -offset:]
                        else:  # Grayscale
                            if offset > 0:
                                result[y_start:y_end, offset:] = result[y_start:y_end, :-offset]
                            else:
                                result[y_start:y_end, :offset] = result[y_start:y_end, -offset:]
                
                elif glitch_type == 1:
                    # RGB channel shift
                    if len(result.shape) == 3:  # Only for color images
                        channel = np.random.randint(0, 3)
                        offset = int(w * current_intensity * 0.1 * np.random.uniform(-1, 1))
                        
                        if offset > 0:
                            result[:, offset:, channel] = result[:, :-offset, channel]
                        elif offset < 0:
                            result[:, :offset, channel] = result[:, -offset:, channel]
                
                elif glitch_type == 2:
                    # Random blocks from the other clip
                    block_h = int(h * 0.05 * np.random.rand())
                    block_w = int(w * 0.2 * np.random.rand())
                    y_start = np.random.randint(0, h - block_h)
                    x_start = np.random.randint(0, w - block_w)
                    
                    other_frame = frame2 if progress < 0.5 else frame1
                    result[y_start:y_start+block_h, x_start:x_start+block_w] = \
                        other_frame[y_start:y_start+block_h, x_start:x_start+block_w]
                
                elif glitch_type == 3:
                    # Noise
                    block_h = int(h * 0.05 * np.random.rand())
                    block_w = int(w * 0.2 * np.random.rand())
                    y_start = np.random.randint(0, h - block_h)
                    x_start = np.random.randint(0, w - block_w)
                    
                    if len(result.shape) == 3:  # Color
                        noise = np.random.randint(0, 255, (block_h, block_w, 3), dtype=np.uint8)
                    else:  # Grayscale
                        noise = np.random.randint(0, 255, (block_h, block_w), dtype=np.uint8)
                    
                    # Apply noise with random alpha
                    alpha = np.random.uniform(0.3, 0.7)
                    block = result[y_start:y_start+block_h, x_start:x_start+block_w]
                    result[y_start:y_start+block_h, x_start:x_start+block_w] = \
                        (block * (1 - alpha) + noise * alpha).astype(np.uint8)
            
            # Gradually transition between clips
            alpha = 1 - progress
            final_result = (result * alpha + frame2 * (1 - alpha)).astype(np.uint8)
            
            return final_result
        else:
            return clip2.get_frame(t)

    return VideoClip(make_frame, duration=clip2.duration + duration)

# Dictionary mapping transition names to functions
transitions = {
    "fade": fade,
    "dissolve": dissolve,
    "wipe_left": wipe_left,
    "wipe_right": wipe_right,
    "wipe_up": wipe_up,
    "wipe_down": wipe_down,
    "slide_left": slide_left,
    "slide_right": slide_right,
    "zoom_in": zoom_in,
    "zoom_out": zoom_out,
    "blur_transition": blur_transition,
    "whip_pan": whip_pan,
    "rotate_transition": rotate_transition,
    "door_wipe": door_wipe,
    "circle_wipe": circle_wipe,
    "diamond_wipe": diamond_wipe,
    "clock_wipe": clock_wipe,
    "split_screen": split_screen,
    "venetian_blinds": venetian_blinds,
    "checkerboard": checkerboard,
    "push": push,
    "luma_wipe": luma_wipe,
    "flip_transition": flip_transition,
    "pixel_dissolve": pixel_dissolve,
    "burn_transition": burn_transition,
    "ripple_transition": ripple_transition,
    "flash_transition": flash_transition,
    "glitch_transition": glitch_transition
}

def apply_transition(clip1, clip2, transition_name="fade", duration=1.0, **kwargs):
    """
    Apply a transition between two clips.
    
    Args:
        clip1: First video clip
        clip2: Second video clip
        transition_name: Name of the transition to apply
        duration: Duration of the transition in seconds
        **kwargs: Additional parameters for the specific transition
    
    Returns:
        A clip with the transition applied
    """
    if transition_name in transitions:
        return transitions[transition_name](clip1, clip2, duration, **kwargs)
    else:
        print(f"Transition '{transition_name}' not found. Using fade.")
        return fade(clip1, clip2, duration)