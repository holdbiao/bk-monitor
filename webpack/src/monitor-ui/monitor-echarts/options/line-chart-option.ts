/* eslint-disable no-mixed-operators */
/* eslint-disable prefer-const */
// @ts-ignore
import { ILegendItem, IChartInstance } from './type-interface'
import MonitorBaseSeries from './base-chart-option'
import deepMerge from 'deepmerge'
import { lineOrBarOptions } from './echart-options-config'
import { getValueFormat, ValueFormatter  } from '../valueFormats'
export default class MonitorLineSeries extends  MonitorBaseSeries implements IChartInstance  {
  public defaultOption: any
  public constructor(props: any) {
    super(props)
    this.defaultOption = deepMerge(deepMerge(lineOrBarOptions, {
      color: this.colors,
      yAxis: {
        axisLabel: {
          formatter: this.handleYxisLabelFormatter
        }
      }
    }, { arrayMerge: this.overwriteMerge }), this.chartOption, { arrayMerge: this.overwriteMerge })
  }
  // 设置折线图
  public getOptions(data: any, otherOptions: any = {}) {
    const { series } = data || {}
    const { boundary, coverSeries } = series?.[0]
    const hasSeries = series && series.length > 0
    const formatterFunc = hasSeries && series[0].data && series[0].data.length
      ? this.handleSetFormatterFunc(series[0].data)
      : null
    let { series: newSeries, legendData } = this.getSeriesData(series)
    // 上下边界处理
    let minBase = 0
    if (boundary?.length) {
      boundary.forEach((item: any) => {
        const base = -item.lowBoundary.reduce((min: number, val: any) => (val[1] !== null
          ?  Math.floor(Math.min(min, val[1]))
          : min), Infinity)
        minBase = Math.max(base, minBase)
      })
      const boundarySeries = boundary.map((item: any) => this.handleBoundarySeries(item, minBase)).flat()
      newSeries = newSeries.map((item: any) => ({
        ...item,
        minBase,
        data: item.data.map((set: any) => {
          if (set?.length) {
            return [set[0], set[1] !== null ? set[1] + minBase : null]
          }
          return {
            ...set,
            value: [set.value[0], set.value[1] !== null ? set.value[1] + minBase : null]
          }
        })
      }))
      newSeries = [...newSeries.map((item: any) => ({ ...item, z: 6 })), ...boundarySeries]
      legendData.push(...boundarySeries.map((item: any) => ({ name: item.name, hidden: true })))
    }
    if (coverSeries?.length) {
      const cover = coverSeries.map((item: any) => this.handleCoverSeries(item, minBase, series?.[0]))
      newSeries = [...newSeries.map((item: any) => ({ ...item, z: 6 })), ...cover]
      legendData.push(...cover.map((item: any) => ({ name: item.name, hidden: true })))
    }
    const [firstSery] = newSeries || []
    const { canScale, minThreshold, maxThreshold }  = this.handleSetThreholds(series)
    const options = {
      yAxis: {
        scale: canScale,
        axisLabel: {
          formatter: newSeries.every((item: any) => item.unit === firstSery.unit) ? (v: any) => {
            if (firstSery.unit !== 'none') {
              const obj = getValueFormat(firstSery.unit)(v - minBase, firstSery.precision)
              return obj.text + (obj.suffix || '')
            }
            return v
          } : (v: number) => this.handleYxisLabelFormatter(v - minBase)
        },
        max: (v: {min: number, max: number}) => Math.max(v.max, maxThreshold),
        min: (v: {min: number, max: number}) => Math.min(v.min, minThreshold),
        splitNumber: 4,
        minInterval: 1,
        axisPointer: {
          label: {
            formatter(params: any) {
              return params.value - minBase
            }
          }
        }
      },
      xAxis: {
        axisLabel: {
          formatter: hasSeries && formatterFunc ? formatterFunc : '{value}'
        }
      },
      legend: {
        show: false
      },
      series: hasSeries ? newSeries : []
    }
    return {
      options: deepMerge(deepMerge(
        this.defaultOption, otherOptions,
        { arrayMerge: this.overwriteMerge }
      ), options, { arrayMerge: this.overwriteMerge }),
      legendData
    }
  }
  private getSeriesData(seriess: any = []) {
    const legendData: ILegendItem[] = []
    const seriesData: any = deepMerge([], seriess)
    const series = seriesData.map((item: any, index: number) => {
      let showSymbol = !!item?.markPoints?.length
      const hasLegend = !!item.name
      const legendItem: ILegendItem = {
        name: String(item.name),
        max: 0,
        min: '',
        avg: 0,
        total: 0,
        color: item.color ||  this.colors[index % this.colors.length],
        show: true
      }
      const unitFormatter = item.unit !== 'none' ? getValueFormat(item.unit || '') : ((v: any) => ({ text: v }))
      const precision = this.handleGetMinPrecision(
        item.data.filter((set: any) => typeof set[1] === 'number').map((set: any[]) => set[1])
        , unitFormatter, item.unit
      )
      item.data.forEach((seriesItem: any, seriesIndex: number) => {
        if (seriesItem?.length && typeof seriesItem[1] === 'number') {
          const pre = item.data[seriesIndex - 1]
          const next = item.data[seriesIndex + 1]
          const curValue = +seriesItem[1]
          legendItem.max = Math.max(legendItem.max, curValue)
          legendItem.min = legendItem.min === '' ? curValue : Math.min(+legendItem.min, curValue)
          legendItem.total = (legendItem.total + curValue)
          const markPonit = item?.markPoints?.find((set: any) => set[1] === seriesItem[0]
          || set === seriesItem[0] || set?.value === seriesItem[0])
          if (markPonit) {
            const itemStyle = markPonit?.itemStyle ||  {
              borderWidth: 6,
              enabled: true,
              shadowBlur: 0,
              opacity: 1
            }
            const symbolSize = markPonit?.symbolSize || 12
            item.data[seriesIndex] = {
              symbolSize,
              value: [seriesItem[0], seriesItem[1]],
              itemStyle
              // label: {
              //   show: false
              // }
            }
          } else {
            const hasNoBrother = (!pre && !next)
            || (pre && next && pre.length && next.length && pre[1] === null && next[1] === null)
            if (hasNoBrother) {
              showSymbol = true
            }
            item.data[seriesIndex] = {
              symbolSize: hasNoBrother ? 4 : 1,
              value: [seriesItem[0], seriesItem[1]],
              itemStyle: {
                borderWidth: hasNoBrother ? 4 : 1,
                enabled: true,
                shadowBlur: 0,
                opacity: 1
              }
            }
          }
        } else if (seriesItem.symbolSize) {
          showSymbol = true
        }
      })
      legendItem.avg = +(legendItem.total / item.data.length).toFixed(2)
      legendItem.total = +(legendItem.total).toFixed(2)
      const seriesItem = {
        ...item,
        type: this.chartType,
        showSymbol,
        symbol: 'circle',
        z: 4,
        smooth: 0,
        unitFormatter,
        precision,
        lineStyle: {
          width: this.lineWidth || 1
        }
      }
      if (item?.markTimeRange?.length) {
        seriesItem.markArea = this.handleSetThresholdBand(item.markTimeRange)
      }
      if (item?.thresholds?.length) {
        seriesItem.markLine = this.handleSetThresholdLine(item.thresholds)
        seriesItem.markArea = deepMerge(seriesItem.markArea, this.handleSetThresholdArea(item.thresholds))
      }
      if (hasLegend) {
        Object.keys(legendItem).forEach((key) => {
          if (['min', 'max', 'avg', 'total'].includes(key)) {
            const set = unitFormatter(legendItem[key], item.unit !== 'none' && precision < 1 ? 2 : precision)
            legendItem[key] = set.text + (set.suffix || '')
          }
        })
        legendData.push(legendItem)
      }
      return seriesItem
    })
    return { legendData, series }
  }
  // 设置阈值线
  private handleSetThresholdLine(thresholdLine: any[]) {
    return {
      symbol: [],
      label: {
        show: true,
        position: 'insideStartTop'
      },
      lineStyle: {
        color: '#FD9C9C',
        type: 'dashed',
        distance: 3,
        width: 1
      },
      data: thresholdLine.map((item: any) => ({
        ...item,
        label: {
          show: true,
          formatter(v: any) {
            return v.name || ''
          }
        }
      }))
    }
  }
  // 设置阈值面板
  private handleSetThresholdBand(plotBands: {to: number, from: number}[]) {
    return {
      silent: true,
      show: true,
      itemStyle: {
        color: '#FFF5EC',
        borderWidth: 1,
        borderColor: '#FFE9D5',
        shadowColor: '#FFF5EC',
        shadowBlur: 0
      },
      data: plotBands.map(item => (
        [{
          xAxis: item.from,
          y: 'max'
        }, {
          xAxis: item.to || 'max',
          y: '0%'
        }]
      )),
      opacity: 0.1
    }
  }

  private handleGetMinPrecision(data: number[], formattter: ValueFormatter, unit: string) {
    if (!data || data.length === 0) {
      return 0
    }
    data.sort()
    const len = data.length
    if (data[0] === data[len - 1]) {
      if (unit === 'none') return 0
      const setList =  String(data[0]).split('.')
      return  (!setList || setList.length < 2) ? 2 : setList[1].length
    }
    let precision = 0
    let sampling = []
    const middle = Math.ceil(len / 2)
    sampling.push(data[0])
    sampling.push(data[Math.ceil((middle) / 2)])
    sampling.push(data[middle])
    sampling.push(data[middle + Math.floor((len - middle) / 2)])
    sampling.push(data[len - 1])
    sampling = Array.from(new Set(sampling.filter(n => n !== undefined)))
    while (precision < 5) {
      // eslint-disable-next-line no-loop-func
      const samp =  sampling.reduce((pre, cur) => {
        pre[formattter(cur, precision).text] = 1
        return pre
      }, {})
      if (Object.keys(samp).length >= sampling.length) {
        return precision
      }
      precision += 1
    }
    return precision
  }

  handleSetThreholds(series: any) {
    let thresholdList = series.filter((set: any) => set?.thresholds?.length).map((set: any) => set.thresholds)
    thresholdList  = thresholdList.reduce((pre: any, cur: any, index: number) => {
      pre.push(...cur.map((set: any) => set.yAxis))
      if (index === thresholdList.length - 1) {
        return Array.from(new Set(pre))
      }
      return pre
    }, [])
    return {
      canScale: thresholdList.every((set: number) => set > 0),
      minThreshold: Math.min(...thresholdList),
      maxThreshold: Math.max(...thresholdList)
    }
  }

  private handleSetThresholdArea(thresholdLine: any[]) {
    const data = this.handleSetThresholdAreaData(thresholdLine)
    return {
      label: {
        show: false
      },
      data
    }
  }

  private handleSetThresholdAreaData(thresholdLine: any[]) {
    const threshold = thresholdLine.filter(item => item.method && !['eq', 'neq'].includes(item.method))

    const openInterval = ['gte', 'gt'] // 开区间
    const closedInterval = ['lte', 'lt'] // 闭区间

    const data = []
    // eslint-disable-next-line @typescript-eslint/prefer-for-of
    for (let index = 0; index < threshold.length; index++) {
      const current = threshold[index]
      const nextThreshold = threshold[index + 1]
      // 判断是否为一个闭合区间
      let yAxis = undefined
      if (openInterval.includes(current.method) && nextThreshold && nextThreshold.condition === 'and'
        && closedInterval.includes(nextThreshold.method) && (nextThreshold.yAxis >= current.yAxis)) {
        yAxis = nextThreshold.yAxis
        index += 1
      } else if (closedInterval.includes(current.method) && nextThreshold && nextThreshold.condition === 'and'
      && openInterval.includes(nextThreshold.method) && (nextThreshold.yAxis <= current.yAxis)) {
        yAxis = nextThreshold.yAxis
        index += 1
      } else if (openInterval.includes(current.method)) {
        yAxis = 'max'
      } else if (closedInterval.includes(current.method)) {
        yAxis = current.yAxis < 0 ? current.yAxis : 0
      }

      yAxis !== undefined && data.push([
        {
          ...current
        },
        {
          yAxis,
          y: yAxis === 'max' ? '0%' : ''
        }
      ])
    }
    return data
  }
  handleBoundarySeries(item: any, base: number) {
    return [
      {
        name: `lower-${item.stack}-no-tips`,
        type: 'line',
        data: item.lowBoundary.map((item: any) => ([item[0], item[1] === null ? null : item[1] + base])),
        lineStyle: {
          opacity: 0
        },
        stack: item.stack,
        symbol: 'none',
        z: item.z || 4
      }, {
        name: `upper-${item.stack}-no-tips`,
        type: 'line',
        data: item.upBoundary.map((set: any, index: number) => ([set[0], set[1] === null
          ? null : set[1] - item.lowBoundary[index][1]])),
        lineStyle: {
          opacity: 0
        },
        areaStyle: {
          color: item.color || '#e6e6e6'
        },
        stack: item.stack,
        symbol: 'none',
        z: item.z || 4
      }]
  }
  handleCoverSeries(item: any, base: number, { boundary, data }: any) {
    if (!(boundary?.length && boundary[0]?.upBoundary?.length && boundary[0]?.lowBoundary?.length && data?.length)) {
      return []
    }
    const resultData: { symbol: string; symbolSize: number; value: any[];
      itemStyle: { borderWidth: number; borderColor: any;
        enabled: boolean; shadowBlur: number; color: string; opacity: number } }[] = []
    // 暂时只做一个上下边界 后期需求再实现
    const [{ upBoundary, lowBoundary }] = boundary
    const len = item.data.length
    const commonPoint = {
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: {
        borderWidth: 2,
        borderColor: item.color,
        enabled: true,
        shadowBlur: 0,
        color: item.color,
        opacity: 1
      }
    }
    for (let seriesIndex = 0; seriesIndex < len; seriesIndex++) {
      const seriesItem = item.data[seriesIndex]
      if (seriesItem?.length && seriesItem[1]) {
        const curX = seriesItem[0]
        const curY = seriesItem[1]
        const curUpperY =  upBoundary.find((set: any[]) =>  set[0] === curX)?.[1]
        const curLowerY =  lowBoundary.find((set: any[]) =>  set[0] === curX)?.[1]
        const hasNext = !!item.data[seriesIndex + 1]?.[1]
        const hasPre = !!item.data[seriesIndex - 1]?.[1]
        if ((curUpperY === null || curUpperY === undefined) || (curLowerY === null || curLowerY === undefined)) continue
        // 如果是独立点则加强显示
        if ((curY === curUpperY || curY === curLowerY) && !hasNext && !hasPre) {
          resultData.push({
            value: [curX, curY + base],
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: {
              borderWidth: 2,
              borderColor: item.color,
              enabled: true,
              shadowBlur: 0,
              color: 'white',
              opacity: 1
            }
          })
          continue
        }
        if (seriesIndex > 0) {
          const preX = item.data[seriesIndex - 1][0]
          const preY = data.find((set: any[]) => set[0] === preX)[1]
          const upperPreY = upBoundary.find((set: any[]) =>  set[0] === preX)?.[1]
          const lowerPreY = lowBoundary.find((set: any[]) =>  set[0] === preX)?.[1]
          const isWithUpper = upperPreY > preY && curY > curUpperY
          const isWithLower = lowerPreY < preY && curY < curLowerY
          // 与上边界、下边界交点
          if (isWithUpper || isWithLower) {
            const [x, y] = this.segmentsIntr({
              a: { x: preX, y: preY },
              b: { x: curX, y: curY },
              c: { x: preX, y: isWithUpper ? upperPreY : lowerPreY },
              d: { x: curX, y: isWithUpper ? curUpperY : curLowerY }
            })
            resultData.push({
              ...commonPoint,
              value: [x,  y + base],
              symbolSize: 0
            })
          }
        }
        if (seriesIndex < len - 1) {
          const nextX = item.data[seriesIndex + 1][0]
          const nextY = data.find((set: any[]) => set[0] === nextX)[1]
          const upperNextY = upBoundary.find((set: any[]) =>  set[0] === nextX)?.[1]
          const lowerNextY = lowBoundary.find((set: any[]) =>  set[0] === nextX)?.[1]
          const isWithUpper = nextY < upperNextY && curY > curUpperY
          const isWithLower = nextY > lowerNextY && curY < curLowerY
          if (isWithUpper || isWithLower) {
            const [x, y] = this.segmentsIntr({
              a: { x: curX, y: curY },
              b: { x: nextX, y: nextY },
              c: { x: curX, y: isWithUpper ? curUpperY : curLowerY },
              d: { x: nextX, y: isWithUpper ?  upperNextY : lowerNextY }
            })
            resultData.push({
              ...commonPoint,
              value: [curX, curY + base],
              symbolSize: 0.5
            })
            resultData.push({
              value: [x,  y + base],
              ...commonPoint,
              symbolSize: 0
            })
            // 如果是连续的上下边界 则中断两点连接
            if (hasNext) {
              resultData.push([x + ((nextX - curX) / 3), null])
            }
            continue
          }
        }
        resultData.push({
          value: [curX, curY + base],
          ...commonPoint,
          symbolSize: 0.5
        })
      } else {
        resultData.push(seriesItem)
      }
    }
    return {
      ...item,
      type: this.chartType,
      showSymbol: false,
      symbol: 'circle',
      smooth: 0,
      lineStyle: {
        width: this.lineWidth || 1
      },
      data: resultData,
      name: `${item.name}-no-tips`
    }
  }
  segmentsIntr({ a, b, c, d }: any) {
    const denominator = (b.y - a.y) * (d.x - c.x) - (a.x - b.x) * (c.y - d.y)
    const x = ((b.x - a.x) * (d.x - c.x) * (c.y - a.y)
      + (b.y - a.y) * (d.x - c.x) * a.x
      - (d.y - c.y) * (b.x - a.x) * c.x) / denominator
    const y = -((b.y - a.y) * (d.y - c.y) * (c.x - a.x)
      + (b.x - a.x) * (d.y - c.y) * a.y
      - (d.x - c.x) * (b.y - a.y) * c.y) / denominator
    return [x, y]
  }
}
