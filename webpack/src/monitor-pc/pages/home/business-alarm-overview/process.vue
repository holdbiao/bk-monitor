<template>
  <div class="process">
    <common-unset :alarm="alarm" v-if="alarm.status === 'unset'"></common-unset>
    <common-noraml :alarm="alarm" v-else-if="alarm.status === 'normal'"></common-noraml>
    <process-serious :alarm="alarm" v-else-if="alarm.status === 'serious' || alarm.status === 'slight'"></process-serious>
  </div>
</template>

<script>
import CommonUnset from './common-unset'
import CommonNoraml from './common-normal'
import ProcessSerious from './process-serious'
export default {
  name: 'process',
  components: {
    CommonUnset,
    CommonNoraml,
    ProcessSerious
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
