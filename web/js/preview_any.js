/*"Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
Augmentstudio.app */

import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

app.registerExtension({
    name: "augment.PreviewAny",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        const previewNodes = [
            "AugmentPreviewAny", "AugmentSwitch",
            "AugmentSHA256", "AugmentRandomNumber", "AugmentUUID",
            "AugmentLoadImage",
        ];
        if (previewNodes.includes(nodeData.name)) {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated ? onNodeCreated.apply(this, []) : undefined;
                this.showValueWidget = ComfyWidgets["STRING"](this, "output", ["STRING", { multiline: true }], app).widget;
                this.showValueWidget.inputEl.readOnly = true;
                this.showValueWidget.serializeValue = async () => "";
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, [message]);
                if (message?.text?.[0] !== undefined) {
                    this.showValueWidget.value = message.text[0];
                }
            };
        }
    },
});
