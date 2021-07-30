export const SnmpVersion = [
    { id: 'snmp_v1', name: 'SNMP Trap V1' },
    { id: 'snmp_v2c', name: 'SNMP Trap V2c' },
    { id: 'snmp_v3', name: 'SNMP Trap V3' }
]
export const AuthPrivList = ['authPriv', 'authNoPriv', 'noAuthNoPriv']

export const excludeValidateMap = {
    authPriv: ['context_name'],
    authNoPriv: ['context_name', 'privacy_protocol', 'privacy_passphrase'],
    noAuthNoPriv: ['context_name', 'privacy_protocol',
      'privacy_passphrase', 'authentication_protocol', 'authentication_passphrase']
}
export const community = 'community'