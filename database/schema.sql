-- TeamMind AI SQLite Schema
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL,
    account VARCHAR(64) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'user',
    avatar_url VARCHAR(512),
    bio VARCHAR(240),
    headline VARCHAR(120),
    portfolio_url VARCHAR(512),
    github_url VARCHAR(512),
    research_interest VARCHAR(240),
    availability VARCHAR(120),
    display_theme VARCHAR(32),
    email VARCHAR(128) UNIQUE,
    email_verified_at DATETIME,
    is_demo BOOLEAN NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    last_login_at DATETIME,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_user_account ON user(account);
CREATE INDEX IF NOT EXISTS ix_user_email ON user(email);

CREATE TABLE IF NOT EXISTS auth_token (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(128) NOT NULL,
    purpose VARCHAR(32) NOT NULL,
    code_hash VARCHAR(128) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_auth_token_email ON auth_token(email);

CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    identity VARCHAR(32),
    degree VARCHAR(32),
    field VARCHAR(32),
    major VARCHAR(64),
    theory_ability TEXT,
    knowledge_score REAL DEFAULT 5.0,
    tech_skills TEXT,
    tool_skills TEXT,
    industry_skills TEXT,
    project_exp TEXT,
    skill_score REAL DEFAULT 5.0,
    comm_ability VARCHAR(16),
    pref_role VARCHAR(64),
    collab_style TEXT,
    team_exp TEXT,
    collab_score REAL DEFAULT 5.0,
    active_tags_json TEXT,
    passive_tags_json TEXT,
    llm_analysis_json TEXT,
    score_breakdown_json TEXT,
    knowledge_final REAL,
    skill_final REAL,
    collab_final REAL,
    raw_source VARCHAR(16),
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_user_profile_user_id ON user_profile(user_id);

CREATE TABLE IF NOT EXISTS community_post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(160),
    content TEXT NOT NULL,
    media_json TEXT,
    tags_json TEXT,
    is_anonymous BOOLEAN DEFAULT 0,
    status VARCHAR(24) DEFAULT 'published',
    llm_tags_json TEXT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_community_post_user_id ON community_post(user_id);
CREATE INDEX IF NOT EXISTS ix_community_post_status ON community_post(status);

CREATE TABLE IF NOT EXISTS post_interaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    post_id INTEGER NOT NULL REFERENCES community_post(id),
    type VARCHAR(32) NOT NULL,
    meta_json TEXT,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_post_interaction_user_id ON post_interaction(user_id);
CREATE INDEX IF NOT EXISTS ix_post_interaction_post_id ON post_interaction(post_id);

CREATE TABLE IF NOT EXISTS post_comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES community_post(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT NOT NULL,
    is_anonymous BOOLEAN DEFAULT 0,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_post_comment_post_id ON post_comment(post_id);

CREATE TABLE IF NOT EXISTS chat_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL REFERENCES user(id),
    user2_id INTEGER NOT NULL REFERENCES user(id),
    last_message_at DATETIME,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_chat_conversation_user1_id ON chat_conversation(user1_id);
CREATE INDEX IF NOT EXISTS ix_chat_conversation_user2_id ON chat_conversation(user2_id);

CREATE TABLE IF NOT EXISTS chat_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES chat_conversation(id),
    sender_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT NOT NULL,
    msg_type VARCHAR(24) DEFAULT 'text',
    read_at DATETIME,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_chat_message_conversation_id ON chat_message(conversation_id);

CREATE TABLE IF NOT EXISTS group_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER REFERENCES team_activity(id),
    group_name VARCHAR(128) NOT NULL,
    member_ids TEXT NOT NULL,
    avg_knowledge REAL DEFAULT 0,
    avg_skill REAL DEFAULT 0,
    avg_collab REAL DEFAULT 0,
    balance_score REAL DEFAULT 0,
    config TEXT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_group_info_activity_id ON group_info(activity_id);

CREATE TABLE IF NOT EXISTS team_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    course_name VARCHAR(120),
    mode VARCHAR(32) DEFAULT 'task_auto',
    status VARCHAR(32) DEFAULT 'draft',
    group_size INTEGER DEFAULT 4,
    task_goal TEXT,
    required_tags_json TEXT,
    required_roles_json TEXT,
    deadline DATETIME,
    class_id INTEGER NOT NULL REFERENCES classroom(id),
    created_by INTEGER REFERENCES user(id),
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_activity_mode ON team_activity(mode);
CREATE INDEX IF NOT EXISTS ix_team_activity_status ON team_activity(status);

CREATE TABLE IF NOT EXISTS team_activity_participant (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES team_activity(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    status VARCHAR(32) DEFAULT 'joined',
    active_tags_json TEXT,
    passive_tags_json TEXT,
    profile_snapshot_json TEXT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_activity_participant_activity_id ON team_activity_participant(activity_id);
CREATE INDEX IF NOT EXISTS ix_team_activity_participant_user_id ON team_activity_participant(user_id);

CREATE TABLE IF NOT EXISTS team_room (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES team_activity(id),
    name VARCHAR(160) NOT NULL,
    description TEXT,
    leader_id INTEGER NOT NULL REFERENCES user(id),
    member_ids_json TEXT,
    desired_tags_json TEXT,
    status VARCHAR(32) DEFAULT 'open',
    group_id INTEGER REFERENCES group_info(id),
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_room_activity_id ON team_room(activity_id);

CREATE TABLE IF NOT EXISTS team_join_request (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES team_activity(id),
    team_id INTEGER NOT NULL REFERENCES team_room(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    message TEXT,
    status VARCHAR(32) DEFAULT 'pending',
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_join_request_activity_id ON team_join_request(activity_id);
CREATE INDEX IF NOT EXISTS ix_team_join_request_team_id ON team_join_request(team_id);

CREATE TABLE IF NOT EXISTS team_confirmation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES team_activity(id),
    group_id INTEGER NOT NULL REFERENCES group_info(id),
    user_id INTEGER NOT NULL REFERENCES user(id),
    status VARCHAR(32) DEFAULT 'pending',
    accept_team BOOLEAN DEFAULT 0,
    accept_role BOOLEAN DEFAULT 0,
    preferred_role VARCHAR(64),
    task_preferences_json TEXT,
    reason TEXT,
    message TEXT,
    handled_by INTEGER REFERENCES user(id),
    handled_note TEXT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_confirmation_activity_id ON team_confirmation(activity_id);
CREATE INDEX IF NOT EXISTS ix_team_confirmation_group_id ON team_confirmation(group_id);
CREATE INDEX IF NOT EXISTS ix_team_confirmation_user_id ON team_confirmation(user_id);
CREATE INDEX IF NOT EXISTS ix_team_confirmation_status ON team_confirmation(status);

CREATE TABLE IF NOT EXISTS task (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name VARCHAR(256) NOT NULL,
    description TEXT,
    difficulty INTEGER DEFAULT 3,
    group_id INTEGER REFERENCES group_info(id),
    assignee_id INTEGER REFERENCES user(id),
    role_required VARCHAR(64),
    estimated_hours REAL DEFAULT 2.0,
    depends_on TEXT,
    deadline DATETIME,
    status VARCHAR(32) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    adjust_times INTEGER DEFAULT 0,
    adjust_history TEXT,
    pending_adjust TEXT,
    create_time DATETIME,
    update_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_task_group_id ON task(group_id);
CREATE INDEX IF NOT EXISTS ix_task_assignee_id ON task(assignee_id);

CREATE TABLE IF NOT EXISTS behavior_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    task_id INTEGER REFERENCES task(id),
    group_id INTEGER,
    progress INTEGER DEFAULT 0,
    submit_status VARCHAR(16),
    active_count INTEGER DEFAULT 0,
    collab_score REAL,
    comment_count INTEGER DEFAULT 0,
    peer_rating REAL,
    tendency VARCHAR(32),
    event_type VARCHAR(32) DEFAULT 'progress',
    detail TEXT,
    record_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_behavior_log_user_id ON behavior_log(user_id);
CREATE INDEX IF NOT EXISTS ix_behavior_log_event_type ON behavior_log(event_type);
CREATE INDEX IF NOT EXISTS ix_behavior_log_record_time ON behavior_log(record_time);

CREATE TABLE IF NOT EXISTS team_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES group_info(id),
    completion_rate REAL DEFAULT 0,
    balance_score REAL DEFAULT 0,
    quality_score REAL DEFAULT 0,
    risk_level VARCHAR(16) DEFAULT 'low',
    detail TEXT,
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_team_report_group_id ON team_report(group_id);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(64) NOT NULL,
    resource VARCHAR(64),
    resource_id INTEGER,
    detail TEXT,
    ip VARCHAR(64),
    create_time DATETIME
);
CREATE INDEX IF NOT EXISTS ix_audit_log_create_time ON audit_log(create_time);
