<template>
  <panel-card class="types-aralm-list" :title="$t('告警类型触发次数分布图')">
    <bk-dropdown-menu
      slot="title"
      @show="dropdownShow"
      @hide="dropdownHide"
      class="title-select"
      ref="dropdown">
      <a slot="dropdown-trigger">
        <span class="title-select-name">{{selectedText}}</span>
        <svg-icon class="title-select-icon"
                  :icon-name="`${isDropdownShow ? 'arrow-up' : 'arrow-down'}`"></svg-icon>
      </a>
      <ul class="bk-dropdown-list" slot="dropdown-content" style="left: -50px">
        <li v-for="item in selectList" :key="item.id">
          <a href="javascript:;" @click="triggerHandler(item)">{{item.text}}</a>
        </li>
      </ul>
    </bk-dropdown-menu>
    <div class="content">
      <ul>
        <template v-for="(item, index) in list">
          <li v-if="index < list.length" :key="index" @click="handleToEventCenter(item.metric_id)">
            <bk-popover :content="`${selectedText} ${item.text}：${item.times} ${$t('次')}`" placement="top">
              <span :class="`left-${index + 1}`" :style="getItemsLeftStyle(item,index)"></span>
              <span :class="`center-${index + 1}`" :style="getItemsCenterStyle(item,index)"></span>
            </bk-popover>
            <span class="right">
              <div class="right-text">
                {{item.text}}
              </div>
              <svg-icon :icon-name="statusIconMap[item.status]"
                        :class="statusClassMap[item.status]"></svg-icon>
            </span>
          </li>
        </template>
      </ul>
    </div>
  </panel-card>
</template>

<script>
import PanelCard from '../components/panel-card/panel-card'
import SvgIcon from '../../../components/svg-icon/svg-icon'

export default {
  name: 'types-alarm-list',
  components: {
    PanelCard,
    SvgIcon
  },
  props: {
    items: {
      type: Array,
      default() {
        return []
      }
    },
    totalWidth: {
      type: Number,
      default: 500
    },
    showExample: {
      type: Boolean,
      default: false
    },
    days: null
  },
  data() {
    return {
      isDropdownShow: false,
      selectedText: this.$t('今日'),
      selectedDate: 1,
      selectList: [
        {
          id: 1,
          text: this.$t('今日')
        },
        {
          id: 7,
          text: this.$t('7日内')
        },
        {
          id: 30,
          text: this.$t('一月内')
        }
      ],
      defaultList: [
        {
          status: 2,
          text: this.$t('发送字节流量'),
          times: 272
        },
        {
          status: 0,
          text: this.$t('5分钟平均负载'),
          times: 136
        },
        {
          status: 2,
          text: this.$t('nathan拨测测试节点平均值可用率'),
          times: 97
        },
        {
          status: 0,
          text: this.$t('nathan拨测测试节点平均值响应时间'),
          times: 95
        },
        {
          status: 2,
          text: this.$t('CPU单核使用率'),
          times: 72
        },
        {
          status: 0,
          text: this.$t('PING不可达告警'),
          times: 44
        },
        {
          status: 2,
          text: this.$t('蓝鲸官网节点平均可用率'),
          times: 31
        },
        {
          status: 0,
          text: this.$t('自定义字符型'),
          times: 21
        },
        {
          status: 2,
          text: 'logTest',
          times: 6
        },
        {
          status: 0,
          text: 'www2',
          times: 3
        }
      ],
      statusIconMap: {
        0: 'back-down',
        1: '',
        2: 'back-up'
      },
      statusClassMap: {
        0: 'right-icon-down',
        1: '',
        2: 'right-icon-up'
      }
    }
  },
  computed: {
    list() {
      if (this.showExample || !this.items.length) {
        return this.defaultList
      }
      return this.items
    }
  },
  watch: {
    days(v) {
      if (v) {
        const date = this.selectList.find(item => item.id === v)
        this.selectedText = date.text
        this.selectedDate = date.id
      }
    }
  },
  methods: {
    dropdownShow() {
      this.isDropdownShow = true
    },
    dropdownHide() {
      this.isDropdownShow = false
    },
    triggerHandler(item) {
      this.selectedText = item.text
      this.selectedDate = item.id
      this.$emit('select', item.id)
      this.$refs.dropdown.hide()
    },
    getItemsLeftStyle(item, index) {
      let next = { times: 0 }
      const totalTimes = this.list[0].times
      if (index !== this.list.length - 1) {
        next = this.list[index + 1]
      }
      return {
        width: `${this.totalWidth * next.times / totalTimes}px`
      }
    },
    getItemsCenterStyle(item, index) {
      let next = { times: 0 }
      const totalTimes = this.list[0].times
      if (index !== this.list.length - 1) {
        next = this.list[index + 1]
      }
      return {
        borderWidth: `35px ${this.totalWidth * (item.times - next.times) / totalTimes}px 0 0`
      }
    },
    handleToEventCenter(metricId) {
      this.$router.push({
        name: 'event-center',
        params: {
          metricId,
          date: this.selectedDate
        }
      })
    }
  }
}
</script>

<style scoped lang="scss">
    @import "../common/mixins";

    $colors: #de6573 #f78b69 #febf81 #ffe7a3 #ffc #ebf7ad #bcd4b7 #85cfb7 #5ba0cb #618ad1;
    $length: 10 !default;

    .types-aralm-list {
      .title {
        &-select {
          float: right;
          height: 19px;
          font-size: $fontSmSize;
          line-height: 19px;
          min-width: 100px;
          text-align: right;
          &-name {
            color: #3a84ff;
            vertical-align: middle;
            cursor: pointer;
          }
          &-icon {
            font-size: 25px;
            color: #3a84ff;
            vertical-align: middle;
            cursor: pointer;
          }
        }

      }
      .content {
        ul {
          margin: 0;
          padding: 0;
          li {
            list-style: none;
            border-bottom: 1px solid #f0f1f5;
            flex: 1;
            min-width: 670px;
            height: 36px;
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap;
            justify-content: flex-start;
            align-items: center;
            font-size: 0;
            background: #fff;

            @include hover();

            @for $i from 1 through $length {
              .left-#{$i} {
                background: nth($colors, $i);
                height: 35px;

                @extend %span;
              }
              .center-#{$i} {
                border-style: solid;
                border-color: nth($colors, $i) transparent transparent;
                background: #fff;

                @extend %center;
              }
            }
            .span,
            %span {
              display: inline-block;
            }
            .center,
            %center {
              height: 0;

              @extend %span;
            }
            .right {
              background: #fff;
              min-width: 82px;
              font-size: $fontSmSize;
              line-height: 35px;
              color: $defaultFontColor;
              text-align: right;
              flex: 1;

              @extend %span;
              &-icon-up {
                color: $seriousColor;
                width: 28px;
                height: 28px;
              }
              &-icon-down {
                color: $normalColor;
                width: 28px;
                height: 28px;
              }
              &-text {
                text-overflow: ellipsis;
                overflow: hidden;
                white-space: nowrap;
                max-width: 80%;
                display: inline-block;
                vertical-align: middle;
              }
            }
          }

        }
      }

    }
</style>
