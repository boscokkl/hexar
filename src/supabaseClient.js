// src/supabaseClient.js
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://piquwumuollziybcwrvs.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpcXV3dW11b2xseml5YmN3cnZzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMxODQ4ODEsImV4cCI6MjA2ODc2MDg4MX0.CdzpGww8XmEdsltdh4D2I5u4KR1y-5fJAur0bTczsKc'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)