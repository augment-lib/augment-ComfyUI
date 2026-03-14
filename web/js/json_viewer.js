/*"Design-focused node suite for ComfyUI."
# Copyright 2026 Augment Studio
Augmentstudio.app */

import { app } from "../../../scripts/app.js";

function syntaxHighlight(json) {
    json = json.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return json.replace(
        /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
        function (match) {
            let cls = "json-number";
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = "json-key";
                } else {
                    cls = "json-string";
                }
            } else if (/true|false/.test(match)) {
                cls = "json-boolean";
            } else if (/null/.test(match)) {
                cls = "json-null";
            }
            return '<span class="' + cls + '">' + match + "</span>";
        }
    );
}

app.registerExtension({
    name: "augment.JsonViewer",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AugmentJsonViewer" || nodeData.name === "AugmentJsonExtract") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated ? onNodeCreated.apply(this, []) : undefined;

                const container = document.createElement("div");
                container.style.cssText = `
                    background:rgb(9, 9, 9);
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                    overflow: auto;
                    max-height: 300px;
                    white-space: pre-wrap;
                    word-break: break-word;
                    color: #ccc;
                `;

                const style = document.createElement("style");
                style.textContent = `
                    .json-key { color:rgb(255, 255, 255); font-weight: 600; }
                    .json-string { color: #fb971d; }
                    .json-number { color: #fb971d; }
                    .json-boolean { color: #fb971d; }
                    .json-null { color: #666; font-style: italic; }
                `;
                container.appendChild(style);

                const pre = document.createElement("pre");
                pre.style.cssText = "margin: 0; font: inherit;";
                pre.innerHTML = '<span style="color:#555;">waiting for data...</span>';
                container.appendChild(pre);

                const widget = this.addDOMWidget("json_display", "customtext", container, {
                    getValue() { return ""; },
                    setValue() {},
                    serialize: false,
                });
                widget.computeSize = function () {
                    return [220, Math.min(container.scrollHeight + 16, 320)];
                };

                this._jsonContainer = pre;
            };

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, [message]);
                if (message?.text?.[0] !== undefined && this._jsonContainer) {
                    this._jsonContainer.innerHTML = syntaxHighlight(message.text[0]);
                    this.setSize(this.computeSize());
                }
            };
        }
    },
});
