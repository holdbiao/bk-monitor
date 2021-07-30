<template>
    <div class="alarm-footer">
        <van-button
            class="alarm-footer-btn"
            :type="type"
            :disabled="disabled"
            :loading="loading"
            @click="handleAlarmCheck">
            <slot />
        </van-button>
    </div>
</template>
<script lang="ts">
import { Prop, Vue, Component, Emit } from 'vue-property-decorator'
import { Button } from 'vant'
@Component({
  name: 'footer-button',
  components: {
    [Button.name]: Button
  }
})
export default class AlarmFooterBtn extends Vue {
  @Prop({ default: 'info' }) private type: string

  @Prop({ default: false }) private disabled: boolean

  @Prop({ default: false }) private loading: boolean

  @Emit('click')
  handleAlarmCheck(e: Event) {
    return e
  }
}
</script>
<style lang="scss" scoped>
/deep/ button[disabled] {
    background-color: #c4c6cc;
    opacity: 1;
    box-shadow: 0px 3px 6px 0px rgba(152,154,157,0.3);
}
.alarm-footer {
    background: linear-gradient(rgba(255,255,255,0) 0, #ffffff 100%);
    // height: 72px;
    position: fixed;
    left: 16px;
    right: 16px;
    bottom: 15px;
    &-btn {
        display: flex;
        width: calc(100vw - 32px);
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        box-shadow: 0px 2px 6px 0px rgba(96,89,79,0.3);
        border: none;
    }
}
</style>
