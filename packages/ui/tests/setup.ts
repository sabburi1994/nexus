import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => cleanup());

// jsdom does not implement the modal dialog API; model the parts the kit relies on.
// (Node environment tests, such as the release check, have no DOM.)
const proto =
  typeof HTMLDialogElement === "undefined"
    ? undefined
    : (HTMLDialogElement.prototype as HTMLDialogElement & { __nxPatched?: boolean });
if (proto && !proto.__nxPatched) {
  proto.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  proto.close = function close(this: HTMLDialogElement) {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
  proto.__nxPatched = true;
}
