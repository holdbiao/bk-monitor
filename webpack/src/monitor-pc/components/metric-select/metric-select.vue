<template>
    <div class="metric-select-wrapper">
        <div class="select-wrapper">
            <bk-select v-model="metric.value" :clearable="false" :popover-min-width="250" @change="handleChange" :class="{ 'right-border-highlight': showLeftBorder }">
                <bk-option style="font-size: 12px;" v-for="(option, index) in data" :key="index" :id="option.name" :name="option.name">
                    <span class="name">{{option.name}}</span>
                    <span style="color: #C4C6CC; margin-right: 5px;" class="alias">{{option.description}}</span>
                </bk-option>
            </bk-select>
        </div>
        <div class="search-wrapper">
            <bk-input @focus="showLeftBorder = true" @blur="showLeftBorder = false" :placeholder="$t('指标')" v-model="metric.keyword" @change="handleSearch"></bk-input>
        </div>
    </div>
</template>
<script>
    import { debounce } from 'throttle-debounce'
    export default {
        name: 'metric-select',
        props: {
            data: {
                type: Array,
                default: () => []
            }
        },
        data () {
            return {
                metric: {
                    value: 'all metric',
                    keyword: '',
                    selectedData: []
                },
                showLeftBorder: false,
                handleSearch () {}
            }
        },
        watch: {
            data: {
                handler (v) {
                    if (v.length) {
                        this.metric.selectedData = v[0].children
                    }
                },
                deep: true
            }
        },
        created () {
            this.handleSearch = debounce(300, this.handleFilter)
        },
        methods: {
            handleChange (v) {
                let children = []
                if (v === 'all metric') {
                    children = this.data.length ? this.data[0].children : []
                } else {
                    const data = this.data.find(item => item.name === v)
                    children = data ? data.children : []
                }
                const result = children.filter(item => item.description.includes(this.metric.keyword) || item.name.includes(this.metric.keyword))
                this.$emit('change', result, v)
            },
            handleFilter (v) {
                const result = this.metric.selectedData.filter(item => item.description.includes(v) || item.name.includes(v))
                this.$emit('change', result, v)
            }
        }
    }
</script>
<style lang="scss" scoped>
.metric-select-wrapper {
    display: flex;
    .select-wrapper {
        font-size: 12px;
        /deep/ .alias {
            margin-right: 10px;
            color: #C4C6CC;
        }
        /deep/ .bk-select {
            max-width: 250px;
            border-radius: 2px 0 0 2px;
        }
        .right-border-highlight {
            border-right-color: #3C96FF;
        }
    }
    .search-wrapper {
        width: 170px;
        /deep/ .bk-form-input {
            border-radius: 0 2px 2px 0;
            border-left: 0;
        }
    }
}
</style>
