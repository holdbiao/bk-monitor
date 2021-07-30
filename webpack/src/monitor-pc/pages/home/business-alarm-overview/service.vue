<template>
  <div class="service">
    <common-unset :alarm="alarm" v-if="alarm.status === 'unset'"></common-unset>
    <common-noraml :alarm="alarm" v-else-if="alarm.status === 'normal'"></common-noraml>
    <service-serious :alarm="alarm" v-else-if="alarm.status === 'slight' || alarm.status === 'serious'"></service-serious>
  </div>
</template>

<script>
import CommonUnset from './common-unset'
import CommonNoraml from './common-normal'
import ServiceSerious from './service-serious'

export default {
  name: 'service',
  components: {
    CommonUnset,
    CommonNoraml,
    ServiceSerious
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
