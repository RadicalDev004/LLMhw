class PCM16Writer extends AudioWorkletProcessor {
  constructor(options) {
    super();
    this.frameSize = options?.processorOptions?.frameSize || 320; // 20ms @16k
    this.buf = new Float32Array(0);
  }
  process(inputs) {
    const input = inputs?.[0]?.[0];
    if (!input) return true;
    const tmp = new Float32Array(this.buf.length + input.length);
    tmp.set(this.buf); tmp.set(input, this.buf.length);
    this.buf = tmp;
    while (this.buf.length >= this.frameSize) {
      const frame = this.buf.subarray(0, this.frameSize);
      this.buf = this.buf.subarray(this.frameSize);
      const out = new ArrayBuffer(frame.length * 2);
      const view = new DataView(out);
      for (let i = 0; i < frame.length; i++) {
        let s = Math.max(-1, Math.min(1, frame[i]));
        view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
      }
      this.port.postMessage(out, [out]);
    }
    return true;
  }
}
registerProcessor("pcm16-writer", PCM16Writer);
