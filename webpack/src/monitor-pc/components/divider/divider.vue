<template>
  <div class="divider" :style="style"></div>
</template>
<script lang="ts">
import { Vue, Prop, Component } from 'vue-property-decorator'

@Component({ name: 'monitor-divider' })
export default class Divider extends Vue {
  @Prop({ default: 1, type: Number }) private readonly width!: number
  @Prop({ default: '16px 20px', type: String }) private readonly margin!: string
  @Prop({ default: '#e0e0e0', type: String }) private readonly color!: string

  private get style() {
    return {
      height: 0,
      margin: this.margin,
      display: 'block',
      borderBottom: `${this.width}px solid ${this.color}`
    }
  }
}
</script>
