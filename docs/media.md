# Media Library

Media records are the assets that schedules assign to displays. Admins and editors manage media from `/admin/media/`.

## Supported Media Types

| Type | Use |
| --- | --- |
| `Image` | Upload a still image for full-screen playback. |
| `Text` | Store text content rendered by the player. |
| `Video` | Upload a local video file for playback. |
| `HTML` | Store HTML content rendered in a sandboxed frame. |
| `YouTube video` | Embed a YouTube URL in the player. |
| `Slider` | Build one or more composed slides with background image, optional foreground image, text, font, animation, and duration. |
| `Neon Sign` | Render full-screen sign text with configurable neon text, frame, and background colors. |

Media can be assigned to many schedules, and schedules can contain many media records. Displays receive media through their active schedules.

## Upload Rules

Image uploads accept:

```text
jpg, jpeg, png, gif, webp
```

Video uploads accept:

```text
mp4, webm, ogg, mov
```

The default upload limit is 100 MB. Change it with `MACROSIGNAGE_MAX_UPLOAD_BYTES`; see [Configuration](configuration.md). Store uploads on persistent storage in production by setting `MACROSIGNAGE_MEDIA_UPLOAD_FOLDER`.

## YouTube URLs

YouTube media accepts common watch, embed, short, and short-link URLs, including:

```text
https://www.youtube.com/watch?v=VIDEO_ID
https://www.youtube.com/embed/VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
https://youtu.be/VIDEO_ID
```

The player adds autoplay parameters for YouTube playback. YouTube content still depends on network access, browser autoplay policies, and YouTube availability.

## HTML Media

HTML media is rendered in an iframe with sandboxing. Use it for trusted internal snippets, dashboards, or embedded widgets that should be isolated from the main admin and player pages.

Treat HTML media as privileged content. Only allow trusted users to create or edit HTML records, and avoid pasting secrets, admin links, or third-party scripts you do not control.

## Slider Media

Slider media supports up to 12 slides. Each slide has:

- Background image: required, using the same image upload rules.
- Foreground image: optional, using the same image upload rules.
- Foreground size: 10 percent through 100 percent, default 50 percent.
- Foreground position: top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, or bottom-right.
- Text: optional text overlay.
- Text position: the same nine-position grid as foreground images.
- Font family: selected from managed Google Fonts.
- Font size: 16 px through 240 px, default 72 px.
- Text animation and foreground animation: none, fade, zoom, bounce, or slide variants from Animate.css.
- Duration: whole seconds, default 10 seconds, maximum 1 hour per slide.

Slider duration is controlled per slide. Regular non-slider media use the schedule default duration.

## Neon Sign Media

Neon sign media stores sign copy in the content field. The player renders it as an uppercase neon tube sign with a glowing frame and textured dark background.

Each neon sign has:

- Text color: controls the neon lettering glow.
- Frame color: controls the sign border and its glow.
- Background color: controls the dark backing behind the sign.

Neon signs use the schedule default duration.

## Fonts

Admins manage available Google Fonts from `/admin/settings/fonts/`. Active fonts appear in slider media forms. A font in use by slider media cannot be deleted until those slides stop using it.

Use the Google Fonts family name, not the stylesheet URL. For example, use `Inter` or `Roboto Condensed`.

## Logo Overlay

Admins manage the global logo overlay from `/admin/settings/logo`. The logo accepts the same image extensions as image media.

Logo settings include:

- Show logo: global toggle for display playback.
- Position: top-left, top-right, bottom-left, or bottom-right.
- Logo file: uploaded image used by the player.
- Remove logo: clears the current file.

When enabled and uploaded, the logo appears over scheduled media, including slider playback. Logo changes trigger player refresh through the content update mechanism.
