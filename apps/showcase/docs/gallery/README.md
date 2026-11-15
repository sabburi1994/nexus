# Design system gallery screenshots

The showcase route `#gallery` (also `#gallery/<theme>/<mode>`, for example `#gallery/finhub/dark`)
renders every `@nexus-agent-framework/ui` component in any app theme, plus a light and dark overview
of all themes. These full page captures use real device emulation (390 px phone, 1440 px desktop):

| File | Theme | Width |
| :--- | :--- | :--- |
| `gallery-390-finhub-light.png` | FinHub, light | 390 px |
| `gallery-390-finhub-dark.png` | FinHub, dark | 390 px |
| `gallery-390-klassesall-light.png` | klassesall, light | 390 px |
| `gallery-desktop-finhub-light.png` | FinHub, light | 1440 px |
| `gallery-desktop-finhub-dark.png` | FinHub, dark | 1440 px |
| `gallery-desktop-predictiveeconomics-light.png` | PredictiveEconomics, light | 1440 px |

Every capture reported a page scroll width equal to the viewport (no horizontal overflow).

Regenerate against a running showcase:

```bash
node apps/showcase/frontend/scripts/capture-gallery.mjs http://127.0.0.1:8080 apps/showcase/docs/gallery
```
