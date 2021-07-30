import { Component as tsc } from 'vue-tsx-support'
import { Component, Prop } from 'vue-property-decorator'
import TestComponent from './test-component'
@Component
export default class MyComponent extends tsc<{a: number}> {
  @Prop() a: number
  c = 3
  render() {
    return <div>
      <TestComponent a={11}/>
    </div>
  }
}
