-- Fix RLS policies for conversations table
DROP POLICY IF EXISTS "conversations_policy" ON conversations;
CREATE POLICY "conversations_policy" ON conversations
FOR ALL USING (true);

-- Fix RLS policies for system_analytics table  
DROP POLICY IF EXISTS "system_analytics_policy" ON system_analytics;
CREATE POLICY "system_analytics_policy" ON system_analytics
FOR ALL USING (true);

-- Alternative: Disable RLS entirely if you prefer (less secure but simpler)
-- ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE system_analytics DISABLE ROW LEVEL SECURITY;
