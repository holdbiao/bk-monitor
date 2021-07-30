<template>
  <div class="os">
    <common-unset :alarm="alarm" v-if="alarm.status === 'unset'"></common-unset>
    <common-noraml :alarm="alarm" v-else-if="alarm.status === 'normal'"></common-noraml>
    <os-serious :alarm="alarm" v-else-if="alarm.status === 'serious' || alarm.status === 'slight'"></os-serious>
  </div>
</template>

<script>
import CommonUnset from './common-unset'
import CommonNoraml from './common-normal'
import OsSerious from './os-serious'
export default {
  name: 'os',
  components: {
    CommonUnset,
    CommonNoraml,
    OsSerious
  },
  props: {
    alarm: {
      type: Object,
      default() {
        return {}
      }
    }
  }
}
</script>
