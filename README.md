# Augment: ComfyUI Node Pack

A design-focused custom node suite for [ComfyUI](https://github.com/comfyanonymous/ComfyUI), built for digital artists and technical designers who need precision, clean outputs, and scalable workflows.

Augment brings grid systems, construction lines, vector conversion, masking, image transforms, and flow control utilities directly into your ComfyUI graph, so you can build production-ready pipelines without leaving the node canvas.

---

## Node Categories

### Vector

Stop exporting pixel-locked assets. The vector nodes bring true scalable output into your generative workflow. Convert any raster image into a clean, editable SVG, or render an SVG back to a high-quality PNG with full alpha, all without leaving ComfyUI.

**PNG to SVG** is built for logo and brand asset pipelines. Run a generated image straight into vectorization and get a production-ready SVG out the other end. Scalable to any size, ready for Illustrator, Figma, or print. **SVG to PNG** works the other way: load any SVG from your input directory and render it to a crisp PNG with alpha channel intact, feeding directly into the rest of your node graph.

Both nodes are powered by the Augment Studio API. An API key is required and available at [augmentstudio.app/pricing](https://augmentstudio.app/pricing). All other Augment nodes work fully offline.


| Node           | Description                                                                                                              |
| -------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **PNG to SVG** | Vectorizes a raster image (PNG, JPG, WebP) into a clean, scalable SVG via the Augment API. Outputs SVG and JSON metadata |
| **SVG to PNG** | Renders an uploaded SVG to a high-quality PNG with full alpha channel. Outputs image and mask tensors                    |


---

### Image Processing

Precision image manipulation nodes built around the objects and assets that matter most in design workflows. **Logo Mask** makes isolating logos and graphic elements dead simple: it auto-detects the background, thresholds the foreground, fills internal holes, and smooths contours giving you a clean usable mask from just an image input, no manual selection required. **Mask Bounding Box** rounds out the masking toolkit by reading any mask and outputting the tight bounding box around its content as pixel coordinates, which can then feed directly into crop, placement, or construction line nodes. The crop nodes make it easy to isolate key subjects. **Face Crop** automatically detects and crops to the largest face in an image with configurable padding and square-crop options, while **Image Crop** handles manual region cropping.

Every node in this section is trigger-aware. Wire them together and your image pipeline runs in exactly the order you designed it, allowing for crazy control. 


| Node                  | Description                                                                                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Logo Mask**         | Generates a clean filled mask from a logo or graphic element. Auto-detects background, fills holes, smooths contours. Outputs mask, mask image, and masked RGB |
| **Mask Bounding Box** | Reads any mask and outputs the tight bounding box around its content as pixel coordinates, with optional padding and threshold control                         |
| **Face Crop**         | Auto-detects the largest face in an image and crops to it, with configurable padding and optional square crop. Outputs crop coordinates and a trigger          |
| **Image Crop**        | Crops an image to a defined region by coordinate and size                                                                                                      |
| **Image Place**       | Composites one image onto another at a specified position                                                                                                      |
| **Invert Image**      | Inverts pixel values across RGB channels                                                                                                                       |
| **Image Rotate**      | Rotates an image by a given angle                                                                                                                              |
| **Image Flip**        | Flips an image horizontally or vertically                                                                                                                      |


---

### Grid & Geometric Drawing

The composition toolkit. These nodes are built for designers who think in systems grids, ratios, axes, and geometry. The **Grid Generator** is the centrepiece: a fully configurable grid engine that outputs a grid image, a mask, and all the dimension data you need to wire into other nodes. Everything else in this section is designed to work alongside it.

**Grid Coords** is the companion node. A layout engine that takes a canvas size and a layout preset (golden ratio, rule of thirds, halves, quadrants) and a named region (top-left, center, bottom-right, etc.), then outputs exact pixel coordinates, dimensions, center point, and a mask for that region. Feed those coordinates directly into placement, crop, or construction line nodes to build compositionally precise workflows without guessing.

The drawing nodes (Line Draw, Circle Draw, Fibonacci Spiral, Construction Line Overlay) all output both an image overlay and a mask, and are rendered at 2x supersampling for clean, anti-aliased results at any resolution.


| Node                          | Description                                                                                                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Grid Generator**            | Generates a grid image with configurable rows, columns, line weight, color, and optional dotted lines. Outputs image, mask, and all dimension values                     |
| **Grid Coords**               | Layout engine. Pick a layout preset (golden ratio, thirds, halves, quadrants) and a region name, get back pixel coordinates, dimensions, center point, and a region mask |
| **Line Draw**                 | Draws an anti-aliased line with presets (diagonals, center axes, outline) or fully custom coordinates. Supports extending lines to canvas edges                          |
| **Circle Draw**               | Draws an anti-aliased circle or ellipse onto a canvas                                                                                                                    |
| **Fibonacci Spiral**          | Renders a golden ratio spiral with optional subdivision rectangles, configurable iterations and line weight                                                              |
| **Construction Line Overlay** | Overlays dotted construction lines (bounding box, center axes, diagonals) onto an existing image from a bounding box input                                               |
| **Shape Edge Detect**         | Detects shape edges for contour and silhouette extraction                                                                                                                |


---

### Color & Effects


| Node                              | Description                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Recolor (Mask)**                | Recolors a masked region to a target color                                                                                      |
| **Blur Average (Dominant Color)** | Blurs or averages a region to its dominant color, great for when you need to grab a spefic color from an image, photo, or logo. |


---

### Primitives

Typed value nodes with trigger in and trigger out, unlike ComfyUI's built-in primitives which are evaluated at graph compile time, these are execution-aware and can be wired into a specific point in your workflow's run order.


| Node       | Description                                |
| ---------- | ------------------------------------------ |
| **Int**    | Integer primitive with trigger passthrough |
| **Float**  | Float primitive with trigger passthrough   |
| **String** | String primitive with trigger passthrough  |
| **Bool**   | Boolean primitive with trigger passthrough |


---

### Variables

Primitives on steroids. Variables are named, persistent values that live across nodes in your workflow. Set them once, read them anywhere, and mutate them through increment, decrement, or reset operations. Built for stateful and iterative workflows where a static primitive isn't enough.


| Node                            | Description                                             |
| ------------------------------- | ------------------------------------------------------- |
| **Variable Set (Number)**       | Assigns a value to a named number variable              |
| **Variable Get (Number)**       | Reads the current value of a named number variable      |
| **Variable Increment (Number)** | Increments a named number variable by a given amount    |
| **Variable Decrement (Number)** | Decrements a named number variable by a given amount    |
| **Variable Reset (Number)**     | Resets a named number variable back to its default      |
| **Variable Set (String)**       | Assigns a value to a named string variable              |
| **Variable Get (String)**       | Reads the current value of a named string variable      |
| **Variable Delete (String)**    | Removes a named string variable from the workflow scope |


---

### Flow Control

By default, ComfyUI evaluates your entire graph at once, everything fires, everything runs. Flow Control breaks that open. These nodes let you sequence, gate, and branch your workflow so that things happen when you decide, not all at the same time. The result is less of a static graph and more of a pipeline you actually control.

**Improved Type Nodes** are the backbone, trigger-aware versions of every major ComfyUI data type that hold their value and only pass it through once a trigger arrives. Chain them together and you get a workflow that moves step by step, each stage waiting on the one before it. **Switch** adds conditional logic: feed it a boolean and it fires down one of two paths, blocking the other entirely, true branching inside a ComfyUI graph.


| Node                    | Description                                                                                                                                                                                           |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Improved Type Nodes** | Trigger-aware nodes for every major ComfyUI data type (Image, Mask, Latent, Model, Clip, VAE, Conditioning, Int, Float, String, Bool) holds a value and only passes it through once a trigger arrives |
| **Switch (Improved)**   | Takes a boolean and fires down either the true or false path, blocking the other conditional branching inside your graph                                                                              |


---

### Data & Intelligence

Every Augment node that does meaningful work outputs structured JSON, coordinates, dimensions, colors, contour counts, layout data, whatever that node knows about what it just did. This section is how you use that data.

**JSON Viewer** lets you inspect the output of any node inline in your graph, no exporting, no guessing. **JSON Extract** lets you pull specific values out by field name and wire them directly into other nodes, prompts, or variables. Today that means tighter, data-driven workflows where one node's output genuinely informs the next. The longer-term direction is feeding this structured data to an LLM so it can make decisions mid-workflow and write values back, closing the loop between generation and design logic in a way ComfyUI doesn't support out of the box.


| Node             | Description                                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------------------------------- |
| **JSON Viewer**  | Inspects and pretty-prints any Augment JSON output inline in the node canvas                                  |
| **JSON Extract** | Pulls a specific value out of any Augment JSON by field name and outputs it as a string ready to wire forward |


---

### Preview & Save

Improved versions of ComfyUI's core I/O nodes, all trigger-aware and all designed to stay out of your way while giving you more. Every node here passes its value through, so you can drop them anywhere in a chain without breaking it.

**Load Image (Improved)** goes well beyond a standard image loader. Alongside the image it outputs dimensions, alpha mask, and individual R/G/B channel masks, all ready to wire into other nodes without any extra processing. **Preview Any** is particularly useful when building or debugging complex graphs: connect it to any text or numeric output a JSON string, a variable, a coordinate and it displays the value inline without interrupting the flow.


| Node                      | Description                                                                                                                                                                |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Load Image (Improved)** | Loads an image and outputs width, height, alpha mask, and individual R/G/B channel masks alongside the image tensor. Supports image override input and trigger passthrough |
| **Preview Image**         | Previews an image inline in the node canvas without writing to the output folder. Passes the image through so the chain keeps running                                      |
| **Save Image (Improved)** | Saves an image to the output folder with a custom filename prefix. Passes the image through with trigger out                                                               |
| **Preview Any**           | Displays any text or numeric value strings, numbers, JSON as readable text in the node UI. Useful for inspecting outputs mid-graph without interrupting the workflow       |


---

## Installation

Augment is not yet listed on the ComfyUI registry. Install it manually by cloning the repository directly into your `custom_nodes` folder.

### Step 1: Clone the repository

```bash
git clone https://github.com/augment-lib/augment-ComfyUI augment
cd augment
```

### Step 2: Install dependencies

```bash
cd augment
pip install -r requirements.txt
```

### Step 3: Restart ComfyUI

Restart ComfyUI. Augment nodes will appear under the **Augment** category in the node search.

---

## Vector Nodes: API Key

The **PNG to SVG** and **SVG to PNG** nodes connect to the Augment Studio API for high-quality vectorization. You will need an API key:

1. Visit [augmentstudio.app/pricing](https://augmentstudio.app/pricing)
2. Create an account and obtain your API key
3. Paste the key into the `api_key` field on the vector nodes

All other nodes work fully offline without an API key.

---

## Requirements

- ComfyUI (latest)
- Python 3.10+
- `opencv-python >= 4.5.0`
- `numpy >= 1.19.0`
- `torch >= 1.9.0`
- `Pillow >= 8.0.0`
- `requests >= 2.25.0`

---

## License

MIT License: Copyright 2026 Augment Studio. See [LICENSE.MD](LICENSE.MD) for details.