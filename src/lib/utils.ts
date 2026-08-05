import { onDestroy } from "svelte";

export class DisposeBag {
    #items: (() => void)[];

    constructor() {
        this.#items = []
        onDestroy(() => {
            for (const item of this.#items) {
                item()
            }
        })
    }

    add(fn: () => void) {
        this.#items.push(fn)
    }
}