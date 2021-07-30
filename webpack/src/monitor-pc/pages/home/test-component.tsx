import { Component as tsc } from 'vue-tsx-support'
import { Component, Prop } from 'vue-property-decorator'
import { Button } from 'bk-magic-vue'
@Component
export default class MyComponent extends tsc<{a: number}> {
  @Prop() a: number
  render() {
    return <div><Button theme="primary"> {this.a}</Button></div>
  }
}
