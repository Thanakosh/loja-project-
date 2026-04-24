export interface WhatsAppAccount {
  id: number
  account_key: string
  provider: string
  display_name: string | null
  linked_phone: string | null
  status: 'disconnected' | 'connecting' | 'connected' | 'error'
  self_chat_mode: boolean
  qr_code_data_url: string | null
  qr_expires_at: string | null
  last_connected_at: string | null
  last_sync_at: string | null
  last_error: string | null
  updated_at: string
}

export interface WhatsAppConnectPayload {
  force_refresh?: boolean
}

export interface WhatsAppMessage {
  id: number
  account_id: number
  cliente_id: number | null
  created_by: number | null
  entity_type: string
  entity_id: number
  message_type: string
  destino: string
  caption: string | null
  media_filename: string | null
  gateway_message_id: string | null
  status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed'
  error_message: string | null
  sent_at: string | null
  delivered_at: string | null
  read_at: string | null
  failed_at: string | null
  created_at: string
  updated_at: string
}

export interface CompartilharOrcamentoWhatsAppPayload {
  telefone?: string
  mensagem?: string
}
