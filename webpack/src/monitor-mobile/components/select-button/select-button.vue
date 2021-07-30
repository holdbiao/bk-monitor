<template>
    <span
        :class="['event-button',{ 'event-button-active': active }]"
        @click="e => $emit('click', e)">
        <i v-show="icon" :class="['icon-monitor', icon]" />
        <span class="text">{{ text }}</span>
    </span>
</template>
<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'

@Component({
  name: 'event-type'
})
export default class EventType extends Vue {
  // 文字
  @Prop({ default: '' }) private text: string

  // icon
  @Prop({ default: '' }) private icon: string

  // 高亮
  @Prop({ default: false }) private active: boolean
}
</script>
<style lang="scss" scoped>
    @import '../../static/scss/variate.scss';
    .event-button {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 32px;
        border-radius: 4px;
        box-shadow: 0px 1px 0px 0px rgba(99, 101, 110, 0.05);
        box-sizing: border-box;
        border: 1px solid #fff;
        background-color: #fff;
        transition: all .2s ease-in-out;
        .text {
            color: $defaultFontColor;
            line-height: 20px;
            font-size: 14px;
            font-weight: 400;
        }
        .icon-monitor {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 16px;
            height: 20px;
            margin-right: 7px;
            font-size: 16px;
        }
        .icon-danger {
            color: #ea3636;
        }
        .icon-mind-fill {
            color: #ff9c01;
        }
        .icon-tips {
            color: #FFD000;
        }
        .icon-user {
            color: #3A84FF;
        }
    }
    .event-button-active {
        border: 1px solid $primaryColor;
        background-color: #e1ecff;
        .text {
            color: $primaryColor;
        }
    }
</style>
