declare module 'wavesurfer.js' {
  interface WaveSurferOptions {
    container: HTMLElement | string
    waveColor?: string
    progressColor?: string
    cursorColor?: string
    height?: number
    responsive?: boolean
    interact?: boolean
    url?: string
  }
  class WaveSurfer {
    static create(options: WaveSurferOptions): WaveSurfer
    destroy(): void
    play(): void
    pause(): void
    setTime(seconds: number): void
    on(event: 'play' | 'pause' | 'ready', cb: () => void): void
    playPause(): void
    registerPlugin<T = any>(plugin: T): T
  }
  export default WaveSurfer
}

declare module 'wavesurfer.js/dist/plugins/regions.esm.js' {
  export interface RegionOptions {
    id?: string
    start: number
    end: number
    color?: string
    drag?: boolean
    resize?: boolean
  }
  export interface RegionsPluginApi {
    addRegion(opts: RegionOptions): any
    clearRegions(): void
  }
  const RegionsPlugin: { create(): any }
  export default RegionsPlugin
}


