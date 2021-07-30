<template>
    <div class="event-tab">
        <van-tabs
            :value="value"
            :class="'event-tab-' + tabList.length"
            @change="handleChangeTab">
            <van-tab
                v-for="(item, index) in tabList"
                :key="index">
                <template #title>
                    <div class="event-tab-text">
                        <span class="title">
                            {{ item.count ? (item.shortTitle ? item.shortTitle : item.title) : item.title }}
                        </span>
                        <span
                            v-show="item.count"
                            class="count"
                        >{{ handleCount(item.count) }}</span>
                    </div>
                </template>
            </van-tab>
        </van-tabs>
    </div>
</template>
<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'
import { Tab, Tabs } from 'vant'
import { ITabItem } from './event-center.vue'

@Component({
  name: 'event-tab',
  components: {
    [Tab.name]: Tab,
    [Tabs.name]: Tabs
  }
})
export default class EventTab extends Vue {
  // tab的配置
  @Prop({ default: () => [] }) readonly tabList: ITabItem[]

  // v-model的值
  @Prop() readonly value: number

  handleCount(count) {
    return count <= 99 ? count : 99
  }

  // 点击tab
  handleChangeTab(val) {
    this.$emit('input', this.tabList[val].value)
    this.$emit('change', this.tabList[val].value)
  }
}
</script>
<style lang="scss" scoped>
    @import '../../static/scss/variate.scss';
    .event-tab {
        border-bottom: 1px solid #dcdee5;
        box-sizing: border-box;
        @for $i from 2 through 3 {
            .event-tab-#{$i}{
                /deep/ .van-tabs__line {
                    height: 2px;
                    background-color: $primaryColor;
                    width: 100% / $i !important;
                }
            }
        }
        &-text {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            font-size: 16px;
            .count {
                display: flex;
                align-items: center;
                justify-items: center;
                // height: 16px;
                padding: 0 4px;
                margin-left: 6px;
                border-radius: 10px;
                font-size: 14px;
                background-color: #C4C6CC;
            }
        }
        /deep/.van-tabs__wrap {
            height: 48px;
            .van-tab {
                font-size: 16px;
                color: #63656E;
                .count {
                    font-size: 14px;
                    color: #fff;
                }
            }
            .van-tab--active {
                color: #313328;
                font-weight: 500;
                .count {
                    background: #3A84FF;
                }
            }
        }
        /deep/ .van-hairline--top-bottom {
            &::after {
                border: none;
            }
        }
    }
</style>
