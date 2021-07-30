<template>
    <div class="chart-container" @click="handleClick">
        <div ref="chart" class="chart" :style="{ backgroundImage: backgroundUrl,backgroundSize: cover ? 'cover' : '' }"></div>
        <slot name="chartCenter"></slot>
    </div>
</template>

<script lang="ts">
    import Highcharts from 'highcharts/highcharts'
    import HighchartsMore from 'highcharts/highcharts-more'
    import HighchartsVariablePie from 'highcharts/modules/variable-pie'
    import { Vue, Prop, Watch, Component } from 'vue-property-decorator'
    HighchartsMore(Highcharts)
    HighchartsVariablePie(Highcharts)

    @Component
    export default class SimpleHighcharts extends Vue {
        chart: Highcharts | null = null
        @Prop({ type: String, default: 'chart' }) constructorType: string
        @Prop({
            type: String,
            default () {
                return `url('${window.site_url}api/signature.png')`
            }
        })
        backgroundUrl: String

        @Prop({
            type: Object,
            default () {
                return { width: 300, height: 300 }
            }
        })
        styles: any

        @Prop({
            type: Boolean,
            default: false
        })
        cover: boolean

        @Prop({
            type: Object,
            required: true
        })
        options: any

        @Prop(Function) callback: (any) => any
        @Prop({
            type: Array,
            default: () => [true, true]
        })
        updateArgs: Array<boolean>

        @Prop({
            type: String,
            default () {
                return this.$t('暂无数据')
            }
        })
        // 空数据提示
        emptyText: string

        @Watch('options', { deep: true })
        omOptionChange (newValue: Object) {
            this.chart.update(Object.assign({}, newValue), ...this.updateArgs)
        }

        created () {
            Highcharts.setOptions({
                global: {
                    useUTC: true
                },
                lang: {
                    noData: this.emptyText
                }
            })
        }

        mounted () {
            const chart: any = this.$refs.chart
            chart.style.minWidth = this.styles.width + 'px'
            chart.style.width = '100%'
            chart.style.height = this.styles.height + 'px'
            this.chart = new Highcharts[this.constructorType](
                this.$refs.chart,
                Object.assign({
                    credits: { enabled: false }
                }, this.options, {
                    chart: {
                        ...this.options.chart,
                        backgroundColor: 'transparent',
                        plotBackgroundColor: 'transparent'
                    }
                }),
                this.callback ? this.callback : null)
        }

        beforeDestroy () {
            try {
                this.chart && this.chart.destroy()
            } catch (error) {
                // console.error(error)
            }
        }

        handleClick (): void {
            this.$emit('click')
        }
    }
</script>

<style lang="scss" scoped>
    .chart-container {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        background-repeat: repeat;
        background-position: left left;
        .chart{
            .highcharts-container {
                z-index: 2 !important;
            }
        }
    }
</style>
