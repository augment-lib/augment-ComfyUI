/*"Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
Augmentstudio.app */

import { app } from "../../../scripts/app.js";

const TITLE_BG = "#443322";
const NODE_BG = "#665533";

const PAID_NODES = [
    "AugmentSVGToPNG",
    "AugmentPNGToSVG",
];

app.registerExtension({
    name: "augment.NodeStyle",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (!PAID_NODES.includes(nodeData.name)) return;

        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            this.color = TITLE_BG;
            this.bgcolor = NODE_BG;
            onDrawForeground?.apply(this, arguments);
        };
    },
});
