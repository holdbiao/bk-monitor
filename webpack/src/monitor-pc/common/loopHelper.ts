class LoopHelper {
  public loopHelper: number
  public timeoutTimer: number
  public intervalTimer: number
  public constructor() {
    this.loopHelper = null
    this.timeoutTimer = null
  }

  public setTimeout(cb, interval) { // 实现setTimeout功能
    const { now } = Date
    const stime = now()
    let etime = stime
    const loop = () => {
      this.timeoutTimer = requestAnimationFrame(loop)
      etime = now()
      if (etime - stime >= interval) {
        cb()
        cancelAnimationFrame(this.timeoutTimer)
      }
    }
    this.timeoutTimer = requestAnimationFrame(loop)
    return this.timeoutTimer
  }

  public clearTimeout() {
    cancelAnimationFrame(this.timeoutTimer)
  }

  public setInterval(cb, interval) { // 实现setInterval功能
    const { now } = Date
    let stime = now()
    let etime = stime
    const loop = () => {
      this.intervalTimer = requestAnimationFrame(loop)
      etime = now()
      if (etime - stime >= interval) {
        stime = now()
        etime = stime
        cb()
      }
    }
    this.intervalTimer = requestAnimationFrame(loop)
    return this.intervalTimer
  }

  public clearInterval() {
    cancelAnimationFrame(this.intervalTimer)
  }
}

const loopHelper = new LoopHelper()
export default loopHelper
