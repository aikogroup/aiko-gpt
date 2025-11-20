--
-- PostgreSQL database dump
--

\restrict c4T7L9VanJfnQxtWyK0QqsijRRqCYm1V02VHTK2Vw1CoVhwCgLJjhKNrdsBy4mo

-- Dumped from database version 16.10
-- Dumped by pg_dump version 18.1 (Ubuntu 18.1-1.pgdg24.04+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_results; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.agent_results (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    workflow_type character varying(50) NOT NULL,
    result_type character varying(50) NOT NULL,
    data jsonb NOT NULL,
    status character varying(50) NOT NULL,
    iteration_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.agent_results OWNER TO aiko_user;

--
-- Name: TABLE agent_results; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.agent_results IS 'Résultats structurés des agents IA';


--
-- Name: COLUMN agent_results.data; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.agent_results.data IS 'Résultats structurés de l''agent en JSONB';


--
-- Name: agent_results_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.agent_results_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.agent_results_id_seq OWNER TO aiko_user;

--
-- Name: agent_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.agent_results_id_seq OWNED BY public.agent_results.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO aiko_user;

--
-- Name: documents; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.documents (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    file_name character varying(255) NOT NULL,
    file_type character varying(50) NOT NULL,
    file_metadata jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.documents OWNER TO aiko_user;

--
-- Name: TABLE documents; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.documents IS 'Métadonnées des documents (sans données extraites)';


--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documents_id_seq OWNER TO aiko_user;

--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.projects (
    id bigint NOT NULL,
    company_name character varying(255) NOT NULL,
    company_info jsonb,
    created_by character varying(100),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.projects OWNER TO aiko_user;

--
-- Name: TABLE projects; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.projects IS 'Projets (1 projet = 1 entreprise)';


--
-- Name: COLUMN projects.company_info; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.projects.company_info IS 'Informations structurées de l''entreprise (secteur, CA, employés, description)';


--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.projects_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projects_id_seq OWNER TO aiko_user;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: speakers; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.speakers (
    id bigint NOT NULL,
    name character varying(255) NOT NULL,
    role character varying(255),
    level character varying(50),
    speaker_type character varying(50) NOT NULL,
    project_id bigint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.speakers OWNER TO aiko_user;

--
-- Name: speakers_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.speakers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.speakers_id_seq OWNER TO aiko_user;

--
-- Name: speakers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.speakers_id_seq OWNED BY public.speakers.id;


--
-- Name: transcripts; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.transcripts (
    id bigint NOT NULL,
    document_id bigint NOT NULL,
    speaker character varying(255),
    "timestamp" character varying(50),
    text text NOT NULL,
    speaker_type character varying(50),
    search_vector tsvector,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    speaker_id bigint
);


ALTER TABLE public.transcripts OWNER TO aiko_user;

--
-- Name: TABLE transcripts; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.transcripts IS 'Interventions extraites avec recherche full-text';


--
-- Name: COLUMN transcripts.search_vector; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.transcripts.search_vector IS 'Vecteur de recherche full-text (mis à jour automatiquement)';


--
-- Name: transcripts_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.transcripts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transcripts_id_seq OWNER TO aiko_user;

--
-- Name: transcripts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.transcripts_id_seq OWNED BY public.transcripts.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    username character varying(100),
    email character varying(255),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO aiko_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO aiko_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: word_extractions; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.word_extractions (
    id bigint NOT NULL,
    document_id bigint NOT NULL,
    extraction_type character varying(50) NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.word_extractions OWNER TO aiko_user;

--
-- Name: TABLE word_extractions; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.word_extractions IS 'Données extraites des rapports Word (besoins et use cases)';


--
-- Name: COLUMN word_extractions.extraction_type; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.word_extractions.extraction_type IS 'Type d''extraction: ''needs'' ou ''use_cases''';


--
-- Name: COLUMN word_extractions.data; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.word_extractions.data IS 'Données structurées extraites (JSONB)';


--
-- Name: word_extractions_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.word_extractions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.word_extractions_id_seq OWNER TO aiko_user;

--
-- Name: word_extractions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.word_extractions_id_seq OWNED BY public.word_extractions.id;


--
-- Name: workflow_states; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.workflow_states (
    id bigint NOT NULL,
    project_id bigint NOT NULL,
    workflow_type character varying(50) NOT NULL,
    thread_id character varying(255) NOT NULL,
    state_data jsonb NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workflow_states OWNER TO aiko_user;

--
-- Name: TABLE workflow_states; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.workflow_states IS 'Checkpoints LangGraph pour partage entre workflows';


--
-- Name: COLUMN workflow_states.state_data; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.workflow_states.state_data IS 'État complet du workflow LangGraph en JSONB';


--
-- Name: workflow_states_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.workflow_states_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workflow_states_id_seq OWNER TO aiko_user;

--
-- Name: workflow_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.workflow_states_id_seq OWNED BY public.workflow_states.id;


--
-- Name: workshops; Type: TABLE; Schema: public; Owner: aiko_user
--

CREATE TABLE public.workshops (
    id bigint NOT NULL,
    document_id bigint NOT NULL,
    atelier_name character varying(255) NOT NULL,
    raw_extract jsonb NOT NULL,
    aggregate jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workshops OWNER TO aiko_user;

--
-- Name: TABLE workshops; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON TABLE public.workshops IS 'Données extraites des fichiers Excel d''ateliers';


--
-- Name: COLUMN workshops.raw_extract; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.workshops.raw_extract IS 'Données brutes extraites du fichier Excel (JSON avec use_case1, use_case2, etc.)';


--
-- Name: COLUMN workshops.aggregate; Type: COMMENT; Schema: public; Owner: aiko_user
--

COMMENT ON COLUMN public.workshops.aggregate IS 'Résultat WorkshopData après traitement LLM (peut être NULL si pas encore traité)';


--
-- Name: workshops_id_seq; Type: SEQUENCE; Schema: public; Owner: aiko_user
--

CREATE SEQUENCE public.workshops_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workshops_id_seq OWNER TO aiko_user;

--
-- Name: workshops_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: aiko_user
--

ALTER SEQUENCE public.workshops_id_seq OWNED BY public.workshops.id;


--
-- Name: agent_results id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.agent_results ALTER COLUMN id SET DEFAULT nextval('public.agent_results_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: speakers id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.speakers ALTER COLUMN id SET DEFAULT nextval('public.speakers_id_seq'::regclass);


--
-- Name: transcripts id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.transcripts ALTER COLUMN id SET DEFAULT nextval('public.transcripts_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: word_extractions id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.word_extractions ALTER COLUMN id SET DEFAULT nextval('public.word_extractions_id_seq'::regclass);


--
-- Name: workflow_states id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workflow_states ALTER COLUMN id SET DEFAULT nextval('public.workflow_states_id_seq'::regclass);


--
-- Name: workshops id; Type: DEFAULT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workshops ALTER COLUMN id SET DEFAULT nextval('public.workshops_id_seq'::regclass);


--
-- Data for Name: agent_results; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.agent_results (id, project_id, workflow_type, result_type, data, status, iteration_count, created_at, updated_at) FROM stdin;
1	6	need_analysis	needs	{"needs": [{"theme": "Analyse prédictive de la satisfaction", "quotes": ["Identification rapide des points de douleur grâce à l'analyse des NPS.", "Mise en œuvre de mesures correctives basées sur des données réelles.", "Renforcement de la fidélisation des clients par une meilleure satisfaction."]}, {"theme": "Gestion automatisée des opérations", "quotes": ["Gain de temps et d'efficacité dans la planification des visites clients.", "Maximisation des opportunités commerciales grâce à une meilleure gestion des visites.", "Personnalisation des interactions client en fonction des données analysées."]}, {"theme": "Automatisation de la production", "quotes": ["Automatisation de l'extraction et analyse des données de production pour réaliser une analyse du cycle de vie.", "Diminution des erreurs humaines lors de l'extraction des données.", "Accélération des processus d'analyse environnementale."]}, {"theme": "Traçabilité et gestion des connaissances", "quotes": ["Facilitation des audits grâce à une documentation claire.", "Amélioration de la visibilité des informations capturées.", "Accélérer la prise de décision grâce à une gestion des connaissances efficace."]}, {"theme": "Optimisation des Données du Marché", "quotes": ["Centralisation des données de marché pour une analyse approfondie.", "Amélioration des stratégies de vente grâce à une veille de la concurrence.", "Réduction des coûts liés à l'analyse manuelle des données dans Excel."]}, {"theme": "Automatisation des Plans de Tournée Commerciale", "quotes": ["Gain de temps et d'efficacité dans la planification des visites clients.", "Maximisation des opportunités commerciales grâce à une meilleure gestion des visites.", "Personnalisation des interactions client en fonction des données analysées."]}]}	rejected	0	2025-11-18 13:53:22.522598+00	2025-11-18 14:05:14.918499+00
9	6	rappel_mission	rappel_mission	{"rappel_mission": "Cousin Surgery est une entreprise spécialisée dans la conception et la fabrication d'implants chirurgicaux textiles pour la chirurgie viscérale, du rachis et bariatrique. Avec une expertise industrielle de plus de 175 ans, elle collabore étroitement avec des professionnels de santé pour innover en matière de dispositifs médicaux implantables. Son siège est situé à Wervicq-Sud, en France, et le groupe est reconnu à l'international dans son domaine d'activité spécialisé et rare."}	validated	0	2025-11-19 08:11:23.945152+00	2025-11-19 08:11:23.945152+00
2	6	need_analysis	needs	{"needs": [{"theme": "Optimisation des Données Commerciales", "quotes": ["Centralisation des données de marché pour une analyse approfondie.", "Amélioration des stratégies de vente grâce à une veille de la concurrence.", "Réduction des coûts liés à l'analyse manuelle des données dans Excel."]}, {"theme": "Automatisation des Tournées Commerciales", "quotes": ["Gain de temps et d'efficacité dans la planification des visites clients.", "Maximisation des opportunités commerciales grâce à une meilleure gestion des visites.", "Personnalisation des interactions client en fonction des données analysées."]}, {"theme": "Automatisation des communications clients", "quotes": ["Amélioration de la rapidité de réponse aux demandes clients.", "Réduction des coûts opérationnels grâce à l'automatisation.", "Amélioration de l'expérience client par une communication fluide."]}]}	validated	0	2025-11-18 14:42:33.416553+00	2025-11-18 15:13:18.46358+00
3	6	need_analysis	use_cases	{"use_cases": [{"id": "uc_1", "titre": "Optimisation des Données Commerciales", "famille": null, "description": "Mettre en place un système d'intelligence artificielle qui recueille, centralise et analyse des données du marché afin d'identifier les tendances, optimiser les décisions commerciales et prévoir de nouvelles opportunités. Ce système utilise des algorithmes de machine learning pour analyser des ensembles de données variés, tout en intégrant des données en temps réel pour alimenter les décisions stratégiques, réduisant ainsi le besoin d'analyses manuelles souvent chronophages.", "ia_utilisee": ""}, {"id": "uc_2", "titre": "Suivi Proactif de la Performance Produit", "famille": null, "description": "Développer un outil d'analyse basée sur l'IA pour surveiller la qualité des dispositifs médicaux tout au long de leur cycle de vie. En utilisant des techniques de machine learning, cet outil peut identifier des anomalies dans les données de production et les retours clients. Cela permet de déclencher des actions correctives avant que des problèmes majeurs ne se produisent, améliorant ainsi la satisfaction client et réduisant les coûts liés aux rappels. La technologie IA aide à modéliser les comportements de marché et à anticiper les besoins d'adaptation des produits.", "ia_utilisee": ""}]}	validated	0	2025-11-18 14:42:33.575255+00	2025-11-18 15:13:18.539004+00
4	6	word_validation	needs	{"needs": [{"theme": "Optimisation des Données Commerciales", "quotes": ["Centralisation des données de marché pour une analyse approfondie.", "Amélioration des stratégies de vente grâce à une veille de la concurrence.", "Réduction des coûts liés à l'analyse manuelle des données dans Excel."]}, {"theme": "Automatisation des Tournées Commerciales", "quotes": ["Gain de temps et d'efficacité dans la planification des visites clients.", "Maximisation des opportunités commerciales grâce à une meilleure gestion des visites.", "Personnalisation des interactions client en fonction des données analysées."]}, {"theme": "Automatisation des communications clients", "quotes": ["Amélioration de la rapidité de réponse aux demandes clients.", "Réduction des coûts opérationnels grâce à l'automatisation.", "Amélioration de l'expérience client par une communication fluide."]}]}	validated	0	2025-11-18 16:28:13.800107+00	2025-11-18 16:28:13.800107+00
5	6	word_validation	use_cases	{"use_cases": [{"id": "uc_1", "titre": "Optimisation des Données Commerciales", "famille": null, "description": "Mettre en place un système d'intelligence artificielle qui recueille, centralise et analyse des données du marché afin d'identifier les tendances, optimiser les décisions commerciales et prévoir de nouvelles opportunités. Ce système utilise des algorithmes de machine learning pour analyser des ensembles de données variés, tout en intégrant des données en temps réel pour alimenter les décisions stratégiques, réduisant ainsi le besoin d'analyses manuelles souvent chronophages.", "ia_utilisee": ""}, {"id": "uc_2", "titre": "Suivi Proactif de la Performance Produit", "famille": null, "description": "Développer un outil d'analyse basée sur l'IA pour surveiller la qualité des dispositifs médicaux tout au long de leur cycle de vie. En utilisant des techniques de machine learning, cet outil peut identifier des anomalies dans les données de production et les retours clients. Cela permet de déclencher des actions correctives avant que des problèmes majeurs ne se produisent, améliorant ainsi la satisfaction client et réduisant les coûts liés aux rappels. La technologie IA aide à modéliser les comportements de marché et à anticiper les besoins d'adaptation des produits.", "ia_utilisee": ""}]}	validated	0	2025-11-18 16:28:13.94697+00	2025-11-18 16:28:13.94697+00
6	6	executive_summary	challenges	{"challenges": [{"id": "E5", "titre": "Gestion proactive des ressources énergétiques", "description": "L'implémentation de solutions d'intelligence artificielle pour le suivi énergétique permettra à l'entreprise de réduire ses coûts opérationnels et d'améliorer son empreinte écologique. En intégrant des systèmes de maintenance prédictive, on pourra garantir une utilisation optimale des ressources énergétiques et éviter les surcoûts liés aux pannes.", "besoins_lies": ["Automatisation des Tournées Commerciales"]}, {"id": "E7", "titre": "Création d'une base de connaissances évolutive", "description": "Établir une base de connaissances enrichie par un chatbot pour centraliser l’information technique et augmenter l'efficacité des équipes. Ce système permettra de répondre rapidement aux questions fréquentes et de réduire le temps consacré à la recherche d'informations, facilitant ainsi la prise de décision.", "besoins_lies": ["Automatisation des communications clients"]}, {"id": "E1", "titre": "Automatisation des communications clients", "description": "La mise en place d'un système d'automatisation des communications permettra de renforcer l'engagement client et d'améliorer la réactivité aux demandes. En utilisant des outils d'IA, l'entreprise pourra personnaliser les messages en fonction des préférences des clients et automatiser l'envoi d'informations pertinentes. Cela conduira à une meilleure satisfaction client et à une réduction des coûts liés aux communications manuelles.", "besoins_lies": ["Automatisation des communications clients"]}]}	validated	0	2025-11-19 08:09:36.976175+00	2025-11-19 08:09:36.976175+00
7	6	executive_summary	recommendations	{"recommendations": [{"id": "R1", "titre": "Centraliser les données de production en temps réel", "description": "Créer une base de données unifiée pour recueillir et analyser toutes les informations de production en temps réel."}, {"id": "R2", "titre": "Développer un système de maintenance prédictive", "description": "Implémenter des technologies IA pour anticiper et prévenir les pannes d'équipements basées sur des analyses de données historiques."}, {"id": "R4", "titre": "Former les équipes à l'IA dans la production", "description": "Encadrer des sessions de formation pour sensibiliser le personnel aux outils IA applicables à la production."}, {"id": "R1", "titre": "Développer une stratégie d’innovation continue", "description": "Mettre en place un processus formel d'innovation pour encourager la créativité et intégrer l'IA dans le développement de nouveaux produits."}]}	validated	0	2025-11-19 08:09:37.102388+00	2025-11-19 08:09:37.102388+00
8	6	executive_summary	maturity	{"maturity_score": 3, "maturity_summary": "L'entreprise démontre une maturité IA intermédiaire, avec une culture numérique active axée sur l'optimisation de plusieurs fonctions, notamment la direction commerciale et la gestion des connaissances. Elle a identifié des besoins spécifiques tels que l'automatisation des communications et la centralisation des données commerciales, et propose des cas d'usage IA pertinents comme l'analyse prédictive des données de marché et le suivi de la qualité produit. Toutefois, l'absence de citations sur la maturité et de détails sur l'infrastructure de données limite l'évaluation complète de sa capacité à exploiter pleinement les outils numériques."}	validated	0	2025-11-19 08:09:37.154542+00	2025-11-19 08:09:37.154542+00
10	6	atouts	atouts	{"atouts": [{"id": 1, "titre": "Culture d'apprentissage et de formation continue", "description": "La culture d'apprentissage ancrée chez Cousin Surgery pourrait favoriser l'intégration réussie de l'IA en permettant aux collaborateurs de s'adapter rapidement aux nouvelles technologies. En s'assurant que chaque membre de l'équipe reçoit une formation spécialisée et peut réintégrer rapidement les processus, l'entreprise pourrait tirer parti des systèmes d'IA pour améliorer l'efficacité et la qualité des produits, tout en réduisant les temps d'adaptation à ces technologies."}, {"id": 2, "titre": "Expertise métier approfondie dans la production médicale", "description": "L'expérience de longue date des collaborateurs en tant que spécialistes des dispositifs médicaux représente un atout majeur qui pourrait catalyser l'intégration de solutions d'IA sur mesure. Cette connaissance métier approfondie permettrait de développer des applications d'IA adaptées aux processus spécifiques, renforçant ainsi l'innovation et l'optimisation des opérations au sein de l'entreprise."}, {"id": 3, "titre": "Écosystème collaboratif avec les professionnels de santé", "description": "La collaboration étroite avec des professionnels de santé pourrait représenter un levier stratégique pour intégrer l'IA dans les dispositifs médicaux. Cette interactivité permettrait d’identifier précisément les besoins cliniques et d'adapter les solutions d'IA aux exigences du terrain, renforçant ainsi la pertinence des technologies développées et améliorant l'acceptation des utilisateurs finaux."}]}	validated	0	2025-11-19 09:02:18.954623+00	2025-11-19 09:02:18.954623+00
11	6	value_chain	value_chain	{"teams": [{"id": "E1", "nom": "Production", "type": "equipe_metier", "description": "Responsable de la fabrication et de la production des produits, gestion des équipes de production, optimisation des processus de fabrication, conformité réglementaire et qualité des produits."}, {"id": "E2", "nom": "Méthodes", "type": "equipe_support", "description": "Équipe en charge de la création et de la validation des documents de production, gestion des standards de production, optimisation des méthodes de travail pour améliorer l'efficacité de la production."}, {"id": "E3", "nom": "Supply Chain", "type": "equipe_support", "description": "Gestion des contrôles d'entrée des matières premières, gestion des stocks et préparation des ordres de fabrication."}, {"id": "E4", "nom": "Qualité", "type": "equipe_support", "description": "S'assure de la conformité des produits aux normes réglementaires, gestion de la documentation qualité et prévention des défauts techniques."}], "activities": [{"id": "A1", "resume": "Fabrication de dispositifs médicaux, gestion des équipes de production, optimisation des processus, conformité réglementaire.", "team_id": "E1"}, {"id": "A2", "resume": "Création et validation des documents de production, gestion des standards, optimisation des méthodes de travail.", "team_id": "E1"}, {"id": "A3", "resume": "Gestion des contrôles d'entrée des matières premières, gestion des stocks, préparation des ordres de fabrication.", "team_id": "E1"}, {"id": "A4", "resume": "Assurance conformité des produits, gestion de la documentation qualité, prévention des défauts techniques.", "team_id": "E1"}], "friction_points": [{"id": "F1", "team_id": "E1", "citation": "En fait, toutes les données que je vous montre, on extrait également tout vers un Excel.", "description": "L'extraction des données vers Excel suggère un manque de centralisation et d'accès en temps réel aux données, ce qui rend difficile une visualisation rapide et efficace des informations essentielles pour le suivi de production."}, {"id": "F2", "team_id": "E1", "citation": "on passe beaucoup de temps donc on essaie toujours de réduire ses délais, d'optimiser les documents faire en sorte que les documents soient le plus clairs possible, le plus ergonomique possible.", "description": "La nécessité d'optimiser les documents indique une absence d'outils adaptés pour organiser et gérer les données, ce qui peut entraîner des erreurs et une inefficacité."}, {"id": "F6", "team_id": "E1", "citation": "Il y a énormément de documents à remplir, tous les jours, pour chaque lot de production.", "description": "Un nombre élevé de documents à remplir montre un manque de données structurées et une surcharge de travail qui nuit à l'efficacité de l'opérateur."}]}	rejected	0	2025-11-19 12:40:26.86018+00	2025-11-19 13:04:09.113895+00
12	6	value_chain	value_chain	{"teams": [{"id": "E1", "nom": "Production", "type": "equipe_metier", "description": "Fabrication et production des implants chirurgicaux textiles, gestion des plannings de production, contrôle qualité, et traçabilité des produits."}, {"id": "E3", "nom": "Qualité", "type": "equipe_support", "description": "Contrôle qualité des matières premières et des produits, gestion de la traçabilité documentaire, et conformité réglementaire."}], "activities": [{"id": "A1", "resume": "Fabrication et production des implants chirurgicaux textiles, gestion des plannings de production, contrôle qualité et traçabilité des produits.", "team_nom": "Production"}, {"id": "A2", "resume": "Contrôle qualité des matières premières et des produits, gestion de la traçabilité documentaire et conformité réglementaire.", "team_nom": "Qualité"}], "friction_points": [{"id": "F4", "citation": "Excel ici on est des pro Excel donc on fait tout en Excel.", "team_nom": "Production", "description": "La dépendance excessive à Excel indique un manque d'outils centralisés et adaptés pour l'analyse des données, ce qui peut conduire à des erreurs et à une gestion inefficace des informations."}, {"id": "F5", "citation": "On extrait tout en fait, donc on a plusieurs requêtes qu'on doit extraire et ensuite du coup on a plein de calculs donc en fait ça c'est les requêtes en orange et ensuite on fait des tableaux croisés dynamiques dans tous les sens, on fait des recherches à revues dans tous les sens pour ensuite utiliser, je pense à la fin, cette courbe là en fait qui nous dit donc ici vous retrouvez les différents secteurs donc préparation, éducation, nettoyage, contre-emballage, conditionnement.", "team_nom": "Production", "description": "La prise de décision basée sur des extractions manuelles de données crée des silos, ce qui empêche une vue d'ensemble et aggrave les problèmes de centralisation des données."}, {"id": "F7", "citation": "Il y a une grande quantité de contrôle qualité, on passe un temps énorme à vérifier les documents pour assurer la conformité, ce qui empêche de se concentrer sur l'amélioration des processus.", "team_nom": "Qualité", "description": "La surcharge liée à la documentation et à la traçabilité rend difficile l'optimisation des opérations, ce qui souligne un manque d'efficacité et une complexité accrue dans l'accès aux données."}]}	validated	0	2025-11-19 14:54:58.491561+00	2025-11-19 14:54:58.491561+00
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.alembic_version (version_num) FROM stdin;
62fa4576e00c
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.documents (id, project_id, file_name, file_type, file_metadata, created_at) FROM stdin;
9	6	6a4a805a-c25a-4ed9-8d51-7ae5f3953dc4_-Cousin-Biotech-x-aiko-Echange-Production-b04e9caa-d79c.pdf	transcript	{}	2025-11-18 13:45:48.889055+00
10	6	4b2b8159-21e8-47da-b470-8efe55ce7b16_atelier_exemple.xlsx	workshop	{}	2025-11-18 13:45:58.048577+00
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.projects (id, company_name, company_info, created_by, created_at, updated_at) FROM stdin;
6	cousin surgery	{"nom": "Cousin Surgery", "secteur": "Fabrication de dispositifs médicaux implantables", "description": "Cousin Surgery est une entreprise spécialisée dans la conception et la fabrication d'implants chirurgicaux textiles pour la chirurgie viscérale, du rachis et bariatrique. Avec une expertise industrielle de plus de 175 ans, elle collabore étroitement avec des professionnels de santé pour innover en matière de dispositifs médicaux implantables. Son siège est situé à Wervicq-Sud, en France, et le groupe est reconnu à l'international dans son domaine d'activité spécialisé et rare.", "nombre_employes": "50-100", "chiffre_affaires": "Non disponible"}	\N	2025-11-18 13:42:40.283523+00	2025-11-18 13:46:59.036077+00
\.


--
-- Data for Name: speakers; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.speakers (id, name, role, level, speaker_type, project_id, created_at, updated_at) FROM stdin;
9	Christella Umuhoza	\N	\N	interviewer	\N	2025-11-18 13:45:48.996465+00	2025-11-18 13:45:48.996465+00
10	Clara DI GIROLAMO	Responsable d'unité de production	métier	interviewé	6	2025-11-18 13:45:49.02299+00	2025-11-18 13:45:49.02299+00
\.


--
-- Data for Name: transcripts; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.transcripts (id, document_id, speaker, "timestamp", text, speaker_type, search_vector, created_at, speaker_id) FROM stdin;
808	9	Christella Umuhoza	00:47	Bonjour. Bonjour, bonjour. Comment allez-vous?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
809	9	Clara DI GIROLAMO	00:52	Bien et vous?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
810	9	Christella Umuhoza	00:53	Bien, bien. Merci d'avoir pris le temps et d'être très réactif sur un message. Alors, je peux... Vous proposer d'abord si nous avons une IA qui prend les notes chez nous est-ce que ça vous va? Je pourrais vous envoyer un compte rendu après donc comme ça, ça nous permet d'échanger vivement sans se soucier de... Ça.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
811	9	Clara DI GIROLAMO	01:22	Marche.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
812	9	Christella Umuhoza	01:25	Ok, génial du coup, le but je ne sais pas si vous avez déjà eu un peu de contexte sur le but de se prendre je suis.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
813	9	Clara DI GIROLAMO	01:35	Revenue lundi après 6 mois de pause.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
814	9	Christella Umuhoza	01:37	Du coup pas beaucoup oui quand même, d'accord 6 mois de pause oui j'étais en congé maternité c'est bon ça et félicitations merci beaucoup ça fait quoi de revenir au travail après 6 mois?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
815	9	Clara DI GIROLAMO	01:55	Je pense qu'en tant que toute maman.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
816	9	Christella Umuhoza	01:56	C'Est pas facile mais ça va j'ai 3 enfants donc Oui, je pense que.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
817	9	Clara DI GIROLAMO	02:03	Chaque reprise est un peu émotive, mais après, ça passe.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
818	9	Christella Umuhoza	02:08	Bon, courage!	interviewer	\N	2025-11-18 13:45:49.042987+00	9
819	9	Clara DI GIROLAMO	02:10	Merci!	interviewé	\N	2025-11-18 13:45:49.042987+00	10
820	9	Christella Umuhoza	02:11	Donc, ok, du coup, je vais détailler quand même et comme ça on pourra se présenter. Ok. Et puis on pourra dérouler, d'accord? D'accord. Donc, aujourd'hui, on se rencontre dans le cadre d'entretien sur le programme appelé un programme EA Booster. C'est un programme que nous faisons en tant que société de conseil et service spécialisé en intelligence artificielle, AICO. AICO a été fondée il y a une année et quelques mois par quatre associés. Deux associés spécialisés, ancien fondateur d'une boîte de conseils appelés INEAD, spécialisés dans tout ce qui est profils techniques, projets techniques, logiciels. Et deux autres, un cofondateur, Manuel Tavi, qui est cofondateur d'OVECIA, qui est une boîte spécialisée dans le développement des modèles data science sur le supply chain, des modèles de provision de stock, demande, croisement, données off et tout ça. Et Manuel Davi a fait l'IA toute sa vie.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
821	9	Christella Umuhoza	03:30	C'est la seule façon de le présenter. C'est un expert habilité sur la France, une des figures reconnues. Et notre CEO, Adrien qui lui aussi a vécu en Chine parce qu'il dirigeait une centrale du INEA Théastèque. Et donc, ils ont cofondé ICO. Il y a quelque temps maintenant, nous sommes une bonne dizaine de consultants et moi, je travaille en tant que AI product manager. Mon métier, c'est vraiment d'identifier les cas d'usage les plus pertinents d'un niveau process, d'un niveau métier, mais d'un niveau aussi logiciel. Je viens d'un background technico-fonctionnel sur le développement des produits. J'ai passé un long séjour aux États-Unis où on fait conception de produits un peu différemment qu'en Europe, pour dire ainsi, mais très riche aussi en aspects business, en termes de valorisation des cas d'usage.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
822	9	Christella Umuhoza	04:31	Je suis personnellement passionnée par la data et tout ce qu'il y a, donc je suis en France depuis pas longtemps, maintenant trois ans. J'ai passé du temps chez ADO, chez Exotech, mais en particulier en parlant de cas d'usage IA, j'ai passé du temps récemment sur des projets ADO pour travailler sur tout ce qui est cas d'usage chez ADO et j'ai rejoint ICO pour appuyer ICO sur le concept d'être une boîte AI native mais aussi pour diversifier mon profil de projet et ne pas rester sur du retail parce que je réalise qu'on y a Les opportunités sont un peu partout, donc je ne voulais pas rester quand même fermée sur un domaine spécifique. Donc, ça fait qu'aujourd'hui, j'accompagne cousins sur cette même perspective. Et donc, le programme IA vient à regarder, évaluer, échanger, découvrir l'environnement de cousins. Nous avons déjà eu plusieurs échanges.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
823	9	Christella Umuhoza	05:40	Ça fait, je pense, celui-ci est le sixième maintenant. Pour découvrir certaines fonctions et donc aujourd'hui le but c'est de découvrir la partie production, de comprendre un peu comment fonctionner, quels sont les membres de vos équipes, mais aussi quels sont les enjeux. Aujourd'hui, est-ce que vous avez imaginé des cas d'usage potentiel de l'IA, est-ce que vous disiez parfois tout ce qui est intelligence artificielle et peut-être que vous avez déjà des opportunités en tête. Mais le but n'est pas d'imaginer directement les cas d'usage, mais c'est plutôt pour que je comprenne un peu le comportement, la jeunesse, votre équipe, et comment vous fonctionnez. Voilà.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
824	9	Clara DI GIROLAMO	06:23	Ok, super, c'est clair. Merci.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
825	9	Christella Umuhoza	06:26	Je vous en prie. Je vais vous présenter du coup.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
826	9	Clara DI GIROLAMO	06:31	Oui, du coup je reviens de 6 mois de congé maternité, du coup je vais essayer de faire au mieux aujourd'hui pour être la plus précise possible dans mon métier mais je pense que j'en ai oublié 80%. Du coup moi ça fait 6 ans que je suis chez Cousin. J'ai commencé en tant qu'ingénieur méthode et ça fait maintenant, c'est ma troisième année du coup, en tant que responsable d'unité de production. J'ai commencé en 2023 en tant que responsable d'unité de production donc je gère deux secteurs sur cinq, je vous en dirai un peu plus après sur la production. Donc j'ai plutôt un profil ingénieur et avant ça j'ai travaillé un an chez Decathlon mais au Bangladesh dans des usines de chaussures. D'accord, intéressant. Et c'est mes seules études professionnelles parce que du coup j'ai fini mes études en 2017.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
827	9	Clara DI GIROLAMO	07:26	Donc je suis encore, je sais pas beaucoup, j'ai 7 ans d'expérience.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
828	9	Christella Umuhoza	07:30	Bah c'est bien quand même. C'est beau quand même dans notre industrie qui est très spécifique. Du coup de décathlon au domaine médical, comment ça se fait ?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
906	9	Clara DI GIROLAMO	42:06	En fait, toutes les données que je vous montre, on extrait également tout vers un Excel. Parce que je suis en train de l'ouvrir, on est très fans des Excel. Alors, on extrait tout sur un Excel et en fait derrière on regarde, vous voyez ici par exemple le temps de prod, donc c'est ce que je vous montrais.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
829	9	Clara DI GIROLAMO	07:43	En fait c'est de production à production, donc au final c'est beaucoup plus exigeant dans le médical, mais au final c'est le même métier de production, on veut coût, qualité, délai, sécurité à la fin, c'est la même chose qu'on produit des chaussures ou des implants. Après le médical est très différent en termes d'exigence réglementaire, en termes de contrôle des salles blanches, etc. On parle pas du tout de la même chose forcément qu'une usine au Bangladesh, beaucoup plus contrôlée, beaucoup plus exigeante, mais ça reste de la production, donc on va dire la base du métier reste la même.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
830	9	Christella Umuhoza	08:17	D'accord. C'est passionnant quand même. En tout cas, en échange avec certaines personnes, je comprends un peu aussi en termes communs, parce que je vois que vous êtes très spécialisé en tout ce qui est textile. Peut-être qu'il y a des points communs entre production décate ou chez vous ? Ou pas du tout ? Vous êtes vraiment...	interviewer	\N	2025-11-18 13:45:49.042987+00	9
831	9	Clara DI GIROLAMO	08:40	En termes de production, on va être, par exemple, là où on va se retrouver, ça va être sur... Alors forcément, ce n'est pas la même chose, mais au niveau des plannings de production, la gestion des équipes, la gestion des compétences, on va pouvoir utiliser les mêmes outils, tout ce qui est les modes opératoires, les standards de production, la sécurité.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
832	9	Clara DI GIROLAMO	09:03	Finalement, on peut utiliser les mêmes outils, les mêmes standards, Après c'est vraiment la manière dont on va le produire et c'est tout ce qui est de la partie contrôle, contrôle, emballage et stérilisation du produit qui va être très différente et toute la partie, on a énormément en fait, à l'inverse d'une production basique, que ce soit un vêtement, une chaussure, où les opérateurs vont travailler uniquement la matière, nous on a je pense 50% de notre métier en tant qu'opérateur qui est de remplir des papiers pour tout ce qui est traçabilité, pour toute la traçabilité justement de la production, quel équipement on a utilisé, quelle est la date de validité de l'équipement, quel instrument de mesure on a utilisé, quels sont les paramètres machines. Quand une personne signe, il faut qu'une autre personne contrôle	interviewé	\N	2025-11-18 13:45:49.042987+00	10
833	9	Clara DI GIROLAMO	09:51	C'est toute cette partie-là où finalement un opérateur doit savoir produire, mais il y a toute une partie qualité documentaire qui est primordiale dans notre production.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
834	9	Christella Umuhoza	10:03	Je n'avais vraiment pas projeté ce niveau de pourcentage en termes de charges de travail à 50% quand même c'est énorme.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
835	9	Clara DI GIROLAMO	10:13	Mais on passe beaucoup de temps donc on essaie toujours de réduire ses délais, d'optimiser les documents faire en sorte que les documents soient le plus clairs possible, le plus ergonomique possible, parce que ce sont des documents qui sont faits dans les bureaux, et une fois qu'on va sur le terrain, forcément il y a toujours un décalage entre les bureaux et le terrain, mais on a de la chance d'avoir la production ici, chez nous, et du coup les équipes travaillent ensemble pour faire les documents les plus ergonomiques possibles, mais il y a énormément de documents à remplir, tous les jours, pour chaque lot de production.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
836	9	Christella Umuhoza	10:43	Tous les jours, j'ai un clos de production. Du coup, si on retourne en arrière, comme ça, ça me permettra de comprendre un peu le fonctionnement sur tout ce workflow. Parlez-moi un peu de la composition de l'équipe.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
837	9	Clara DI GIROLAMO	10:57	Alors, la composition de l'équipe, donc je parle uniquement production. On est à peu près, on va dire une trentaine d'opératrices. Et au management, on est cinq. Donc, il y a un responsable de production qui est vraiment leader de la production. Il y a deux... Non, moi en fait, je suis responsable d'unité de production. On est un peu deux en binôme, mais on va dire qu'il y a Jonathan qui est le vrai responsable de production. Et moi, j'ai deux autres. Donc, on va dire il y a cinq secteurs. Attendez, il faut que je m'en mette. Préparation, fabrication, remballage, nettoyage. Il y a cinq secteurs. J'en ai deux, il en a trois, mais c'est plus lui le vrai responsable de production, ça serait plus Jonathan.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
838	9	Christella Umuhoza	11:48	D'accord, ok.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
839	9	Clara DI GIROLAMO	11:50	On va dire que je suis plus chef d'équipe, amélioration continue, une chose comme ça.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
840	9	Christella Umuhoza	11:54	Vous voyez vraiment en termes microscopiques tout ce qui se passe versus ce qu'il voit et puis vous appuyez ensemble même si c'est lui votre responsable, j'imagine.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
841	9	Clara DI GIROLAMO	12:05	C'Est pas... Bah du coup non, c'est pas mon responsable Jonathan, vous avez Xavier, monsieur Lanciot, je pense Xavier Lanciot. Xavier est notre responsable à tous les deux en fait et Jonathan et moi on travaille plutôt en binôme du coup. On travaille plutôt en binôme. En fait, moi, l'idée, c'était quand j'ai récupéré la salle blanche, une partie de la salle blanche du bas. Je vous expliquerai après. En fait, la salle blanche, c'est sur deux étages, rez-de-chaussée et premier étage.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
842	9	Christella Umuhoza	12:29	C'est une bonne question parce que j'ai beaucoup entendu parler de la salle blanche. Donc, j'attendais quelqu'un qui ait bien l'habilité à m'expliquer ces salles.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
843	9	Clara DI GIROLAMO	12:41	Eh bien, je vais vous le faire, c'est très simple. Le produit, en fait, quand on commence... Donc, vous retenez, on est 30 opératrices, 5 personnes au management. Donc, on va dire Jonathan et moi, un peu en binôme, mais pour moi, le responsable de production, c'est Jonathan. Et ensuite, il y a deux... On va dire deux chefs d'équipe et une personne qui est entre le chef d'équipe et le responsable de production. On appelle ça chez nous, en gros, il y a le responsable de production, copilote et animateur.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
844	9	Clara DI GIROLAMO	13:11	Dans la hiérarchie ça fait responsable de prod, copilote et animateur donc ça c'est on va dire la partie main d'oeuvre et ensuite donc au niveau de la salle blanche c'est assez facile donc vous avez rencontré je pense les personnes de la supply il me semble vous avez déjà vu donc eux s'occupent de tout ce qui est donc réception de matière ils vont nous les transmettre en salle blanche, nous on va commencer par les contrôles d'entrée.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
922	9	Christella Umuhoza	52:06	Et du coup, vous avez une base de données sur l'historique des formations données d'un profil à un autre?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
924	9	Christella Umuhoza	52:32	Vous le dites comment du coup? Validé ou pas?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
845	9	Clara DI GIROLAMO	13:38	Les contrôles d'entrée sont faits en salle blanche, donc la partie supply va faire tout ce qui est contrôle d'entrée, partie documentaire, et nous on va par exemple si on reçoit du tricot, on va venir tester les tricots au banc de traction pour avoir la résistance d'un tricot, l'allongement d'un tricot, Là c'est de la même manière, il y a beaucoup de documents à remplir, donc ça c'est toute la partie on va dire contrôle d'entrée, donc on contrôle du tricot, on contrôle des aiguilles, on contrôle des éléments en silicone, on va vraiment contrôler tous les éléments qu'on va utiliser ensuite pour nous, toute la matière première qu'on va utiliser ensuite pour nos produits. Ça c'est la partie contrôle d'entrée.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
846	9	Clara DI GIROLAMO	14:16	Ensuite donc nous on stocke, donc les composants sont stockés, une partie des composants est stockée, soit on stocke matière première, donc en partie supply logistique, soit une partie est stockée directement en salle blanche ce qu'on appelle un bord de ligne donc ça va être stocké en salle blanche chez nous ensuite donc en fonction du planning qui va nous arriver donc ça c'est la partie ordonnancement qui est faite donc nous on va voir des ordres de fabrication on va voir donc du coup des ordres de fabrication à préparer donc moi mon équipe en bas du coup ce qu'on appelle la préparation donc la salle de préparation en bas on va préparer des OFs. OFs c'est un ordre de fabrication.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
847	9	Clara DI GIROLAMO	14:59	Sur cet OF qui vient de CILOB, vous allez entendre parler de CILOB, On va nous dire qu'il faut 2 composants A, 3 composants B, 5 composants C. Donc moi, mon équipe, ils vont préparer tout ça. En fait, c'est vraiment la partie préparation de commandes, tout simplement. Donc on va préparer les composants et on va également préparer la partie documentaire. Donc c'est ce qu'on va appeler relevé de paramètres, relevé de contrôle. C'est deux feuilles distinctes où on va remplir tous les paramètres dont je vous parlais, les paramètres machines. Donc le numéro d'équipement qu'on utilisait, les dates de validité, les numéros d'instruments de mesure, donc les réglés, etc. Et par exemple les températures, les pressions des machines, etc. Ça va être rempli dans un relevé de paramètres.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
848	9	Clara DI GIROLAMO	15:48	Et on a également un relevé de contrôle, donc tout au long de la fabrication, les produits vont être contrôlés et on va rentrer ces données dans des relevés de contrôle. Donc le métier de mon équipe, en bas, c'est de préparer cette partie documentaire. On rassemble tout, les documents, les composants, et tout ça ensuite par en salle blanche du haut, justement.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
849	9	Clara DI GIROLAMO	16:11	Avant de partir en salle blanche du haut dans mon équipe également en bas donc en fait nos produits vous avez dû entendre parler c'est soit des tricots soit des tresses les tricots ils nous arrivent directement de l'extérieur les tresses nous ici on reçoit du fil et ensuite on a des tresseuses donc on fait nos propres tresses Donc ça c'est également mon équipe donc en bas, on transforme en fait la matière première de fil, on la transforme en tresse, on stocke les tresses et quand on doit préparer une commande, si une commande demande la tresse numéro 1 par exemple, je vais prendre mon stock de tresse numéro 1, je vais la mettre dans un bac et je vais tout faire monter à l'étage. En gros ça se passe comme ça. C'est clair pour vous?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
850	9	Christella Umuhoza	16:57	Oui, c'est très clair. Maintenant, je suis en train de visualiser exactement comment ça marche. Est-ce que vous avez	interviewer	\N	2025-11-18 13:45:49.042987+00	9
851	9	Clara DI GIROLAMO	17:09	Est-ce que vous voulez que je vous le partage maintenant ou plus tard?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
852	9	Christella Umuhoza	17:12	Plus tard, si vous voulez, parce que là, je ne sais pas comment ça marche. Si vous pouvez peut-être m'envoyer le document ou d'autres, peut-être qu'au fil de la conversation, on va voir qu'on en a besoin. Mais c'est très clair. Merci beaucoup, merci beaucoup pour ce schéma. Et du coup, parlez-moi du coup sur ce process de documentation, comment vous faites, comment vous y mettez entre les revues, les premiers drafts et tout ça. Et puis parlez-moi d'autres outils que vous utilisez en parallèle sur tout ce workflow que vous venez de me décrire.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
853	9	Clara DI GIROLAMO	17:51	Au niveau de la documentation, c'est le service méthode qui les fournit. J'ai passé trois ans à être au service méthode. Le travail d'un ingénieur méthode, ça va être d'aller sur le terrain, de discuter avec les équipes de production et d'écrire ces documents en fonction des machines qu'on va utiliser, en fonction du flux du produit, on doit respecter toute une documentation qui doit être toujours la même, on utilise toujours évidemment le même template pour tous les produits, comme ça d'un produit à l'autre, une opératrice n'est pas perdue, elle sait toujours remplir son document parce que c'est toujours les mêmes documents qu'on va fournir.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
854	9	Christella Umuhoza	18:37	D'Accord et vous utilisez quoi comme logiciel?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
855	9	Clara DI GIROLAMO	18:42	Excel ici on est des pro Excel donc on fait tout en Excel j'ai.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
856	9	Christella Umuhoza	18:48	Compris, je voulais voir si vous avez peut-être un autre truc, outil secret mais je comprends que l'Excel a sa valeur chez Cousins en tout cas oui, on.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
857	9	Clara DI GIROLAMO	18:59	Est tous formés à Excel, on utilise tous Excel pour tout Donc on existe tous Excel et en fait toutes les données de machines etc. Ça provient de validations que les ingénieurs méthode font en parallèle pour valider les machines. Dès qu'on rentre une machine on doit la valider de manière médicale et du coup on en sort des paramètres machines qu'on utilisera ensuite en production et c'est.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
858	9	Christella Umuhoza	19:30	Ces paramètres là qu'on... Quoi valider de manière médicale ? Parlez-moi un peu de ça, parce que moi, qui ne viens pas du monde médical, j'ai du mal à visualiser.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
859	9	Clara DI GIROLAMO	19:39	En fait, quand on valide, alors là, c'est mes souvenirs du coup d'Argélio Metton, quand on valide une machine, en fait, par exemple, si je prends une scelleuse, Donc on sait qu'une cellule elle va avoir trois paramètres, donc température, temps et pression. Donc en fait notre travail ça va être devenu, donc on appelle ça QOP et QPP. QOP c'est qualification opérationnelle du procédé, QPP c'est qualification de performance du procédé. Donc en QOP en fait on va venir chercher les paramètres minimaux et paramètres maximaux dans lequel on va pouvoir utiliser la machine en production. On va réaliser d'abord un plan d'expérience, on va essayer de trouver les paramètres qui correspondent le plus. Une fois qu'on a validé ces paramètres en plan d'expérience, on va partir en QOP.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
860	9	Clara DI GIROLAMO	20:31	Où on valider les paramètres minimaux et maximaux, avec un certain échantillonnage à respecter, et une fois qu'on a ces paramètres min et ces paramètres max, on part en QPP, donc qualification de performance du procédé, et là en fait on doit répéter, on a figé des paramètres min, paramètres max, là en QPP on va se mettre au milieu, par exemple si je suis entre, alors je dis vraiment pif, J'ai validé machine entre 10 et 20 secondes, là en QPP je vais mettre à 15 secondes et je vais faire trois lots différents avec trois opératrices différentes pour voir, avec normalement même trois lots de matières différentes, pour voir que ce n'est pas opérateur dépendant ni matière dépendant et que mon procédé est répétable.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
861	9	Clara DI GIROLAMO	21:20	Et c'est de là que ces paramètres sont définis et validés par les ingénieurs méthode, et c'est à partir de ces paramètres qu'on les met dans nos documents de production. Comme ça, une opératrice sait que le scellage, elle doit toujours le faire pendant 15 secondes par exemple. Mais si jamais elle le fait à 16 secondes, comme nos documents sont validés jusqu'à 20 secondes, on est toujours dans nos paramètres et on est toujours bon selon la validation.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
862	9	Christella Umuhoza	21:51	Je vois un peu l'idée. Du coup, ok, là c'est la validation médicale. Parlons un peu de... Vous travaillez beaucoup avec la R&D?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
863	9	Clara DI GIROLAMO	22:06	La production, les méthodes, oui. Les méthodes vont travailler avec la R&D, la production un peu moins. La production, le seul cas où on va travailler avec eux, c'est par exemple, parfois ils doivent faire des produits, pas beaucoup la R&D. Parfois ils doivent faire des produits, ils vont nous demander de l'aide pour faire une couture, pour utiliser une machine, choses comme ça, mais pas beaucoup avec la R&D.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
864	9	Christella Umuhoza	22:32	Du coup, parce que moi, de ce que j'avais compris, en fait, il y a production et méthode qui sont genre comme un département. Qui travaillent en parallèle, mais c'est plutôt, vous êtes vraiment à part et méthode est vraiment à part.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
865	9	Clara DI GIROLAMO	22:47	Oui, en fait, c'est vraiment deux services complètement différents. Il y a vraiment le service de production, où nous, en fait, notre travail, c'est de, on a l'ordonnancement qui nous donne un planning de prod, et nous, on doit sortir les produits avec le bon délai, bonne qualité, sans avoir fait d'accident de travail. Et j'ai dit quoi, c'est le bon coût forcément, donc en respectant des temps standards. Ça c'est vraiment notre métier de production et les méthodes, ça va plutôt être... Alors il y a la partie validation comme je viens de vous expliquer, la partie documentation de production, donc tous les documents, les standards de production, les documents que nous on va utiliser en production, les recettes en fait. Les SOP, ça c'est eux qui vont nous les fournir.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
866	9	Clara DI GIROLAMO	23:28	La partie aussi, il faut acheter des machines pour le futur, il faut acheter ces machines, il faut les valider, il faut imaginer les plans de la salle blanche, etc. Ça c'est plutôt eux qui vont construire des nouvelles salles blanches par exemple aussi. Et étant de la salle blanche, c'est plutôt eux qui vont faire des essais sur les produits. Ça c'est plutôt toute la partie d'ingénieur de méthode. Donc c'est quand même deux métiers bien différents. En fait évidemment on travaille ensemble, mais c'est deux métiers bien différents.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
867	9	Christella Umuhoza	23:57	D'accord. Et du coup, en termes de planning, vous opérez comment ? Vous m'avez décrit un workflow, j'imagine qu'il y a beaucoup de planning dessus, sur qui fait quoi, livraison, type produit, comment vous arrivez à gérer ça en interne ? Encore, je sens l'excès d'arrivée, Est-ce qu'il y a d'autres méthodes peut-être? Ok, d'accord. Est-ce que vous pouvez montrer un fichier Excel par exemple?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
868	9	Clara DI GIROLAMO	24:30	Alors si, il y a Excel, mais du coup on utilise Syllab aussi maintenant. On utilise de plus en plus Syllab qui est autre ERP forcément, mais c'est pas lui qui nous sort encore les playlists.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
869	9	Christella Umuhoza	24:41	Ok, je peux voir Syllab en termes d'interface, comment ça se présente de votre côté?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
870	9	Clara DI GIROLAMO	24:53	Que je me reconnecte. Syllops ça se présente comme ça, alors après ça c'est mon écran de production, il y a plein d'autres écrans, soit pour la supply, pour les achats, pour la qualité, chacun va avoir son écran différent, mais Syllops ça va se présenter comme ça.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
871	9	Christella Umuhoza	25:27	Et en termes de, disons que vous voulez créer un plan de, je dis n'importe quoi, vous pouvez me corriger, un plan de production, C'est comme ça que vous l'appelez peut-être. En fait, j'essaie de voir vous, comment vous opérez quand vous avez différents intervenants sur le workflow que vous m'avez décrit. Comment vous interagissez ensemble en fait sur cela ?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
872	9	Clara DI GIROLAMO	25:54	En fait, l'ordonnancement, en fait, là, il faudrait plus que vous interrogez du coup le service ordonnancement parce que c'est vraiment eux qui font toute la partie planning et je pense que je voudrais aider. Je vous dirais des bêtises, mais en fait l'ordonnancement il va avoir toute la partie commandes qui va être entrée dans Sylum, donc on va ensuite créer des... Il y a des ordres de fabrication qui vont être créés. Et en fait ensuite on en extrait une requête... Alors attendez... Je pense que ça doit être celui-ci. En fait sur Syllab on va créer tout ce qui est des requêtes. Ces Syllab vont aller chercher dans toutes les différentes tables qui existent. Alors là oui c'est un peu long.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
873	9	Clara DI GIROLAMO	27:05	En fait on va voir, ben ici l'OF a été créé tel jour, c'est tel code d'OF, le numéro de l'article, ça je pense que c'est pour la mise en carton, ça c'est le numéro d'opération, ça c'est, donc je vous disais il y a 5 secteurs chez nous, donc ici en fait vous aurez toujours CC01, 2, 3, 4, 5 en fonction du secteur dans lequel vous travaillez. Le nombre de produits à fabriquer, les temps théoriques, les temps réels, est-ce que l'OF est fini ou pas fini, et en fait ce qu'on fait c'est que nous on va faire une extraction de ça sur Excel, et ça je peux vous le montrer, ensuite on va arriver dans... Où est-ce	interviewé	\N	2025-11-18 13:45:49.042987+00	10
874	9	Christella Umuhoza	27:54	Mais ce que je dis là, c'est que vous avez une gestion de classification où les mettre et puis... Oui, c'est ça.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
923	9	Clara DI GIROLAMO	52:20	Non, en fait, moi, ce que je serais capable de dire aujourd'hui, je serais capable de dire que j'ai tel ou tel process et telle ou telle personne est validée ou non sur ce process. Ça, je suis capable de le dire.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
875	9	Clara DI GIROLAMO	28:02	Et en fait, après, je pense que c'est dans... Est-ce que c'est dans GSTOR, je ne sais plus. Est-ce que j'aimerais vous montrer un Excel. Projection de stock, c'est ça. Un BIC Lomb, voilà c'est ça. Projection de stock fini V3, alors ils sont certainement à la V3. En fait, vous voyez ensuite ce que je vous ai montré du coup, ici. On l'extrait ici. Et du coup, c'est pas libre élection.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
876	9	Clara DI GIROLAMO	29:10	Voilà, on extrait tout en fait, donc on a plusieurs requêtes qu'on doit extraire et ensuite du coup on a plein de calculs donc en fait ça c'est les requêtes en orange et ensuite on fait des tableaux croisés dynamiques dans tous les sens, on fait des recherches à revues dans tous les sens pour ensuite utiliser, je pense à la fin, cette courbe là en fait qui nous dit donc ici vous retrouvez les différents secteurs donc préparation, éducation, nettoyage, contre-emballage, conditionnement Oui, en fait, je vois du coup, par exemple, en semaine 15, donc cette semaine, j'ai 266 heures de travail en fabrication. Parce qu'en fait, Sylop, du coup, il va savoir me faire le tri entre les OFs terminés, les OFs commencés, les OFs non commencés, pour quelle semaine c'est à faire, et ensuite on fait tous nos calculs et on en sort tout ça.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
877	9	Christella Umuhoza	30:02	D'accord, ok.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
878	9	Clara DI GIROLAMO	30:05	Mais pour l'instant, ce n'est pas CILOB qui nous fait notre planning. Il faudrait que je vous explique. Il y a cinq secteurs. Vous voyez les noms ici. Préparation, vérification, nettoyage, contrôle emballage, conditionnement. On ne travaille pas dans tous les secteurs. Par exemple, moi, cette semaine, En préparation, je vais préparer des OF qui doivent partir pour la semaine 18 au conditionnement. En fait, les OF que je vais travailler cette semaine, les mêmes arriveront en semaine 18, donc trois semaines plus tard au conditionnement.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
879	9	Christella Umuhoza	30:44	D'accord.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
880	9	Clara DI GIROLAMO	30:46	C'est pour ça qu'il y a toujours un décalage en fabrication. Cette semaine, ils vont travailler pour la semaine... On est en semaine 15, donc ils travaillent pour la semaine 17. Donc, en fait, tout est à chaque fois décalé. C'est un peu une mécanique difficile. En fait, ce qui est complexe chez nous, on n'est pas sur une ligne de production. C'est-à-dire que quand je commence un produit, c'est pas une chaussure où j'ai cinq formes d'opérateurs qui sont à la ligne l'un à la suite de l'autre. Quand je le commence, je n'ai pas un temps qui va me dire que c'est fini en trois minutes et j'ai un produit qui sort toutes les trois minutes. En fait, c'est-à-dire que j'ai des secteurs différents et on a beaucoup de temps d'attente. Ce qu'on essaie de travailler dessus, on a beaucoup de temps d'attente entre les secteurs.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
881	9	Clara DI GIROLAMO	31:29	Une commande que moi, par exemple, j'ai terminée en préparation, je vais l'avoir terminée aujourd'hui et bien peut- être qu'on va la travailler en fabrication deux jours plus tard.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
882	9	Clara DI GIROLAMO	31:38	Donc en fait on a beaucoup de stock en cours de production, ce qui fait qu'on a toujours des plannings qui sont décalés et si l'homme n'est pas capable de calculer pour l'instant, par exemple si on dit il y a 5 minutes de préparation, 10 minutes de couture, 5 minutes de nettoyage, lui il va faire 5 plus 10 plus 5 ok il faut 20 minutes donc si mon OEF va être fini pour le 11 avril et ben je peux le commencer le 10 avril et en 5 et en 20 minutes il sera fait ce qui se passe pas du tout comme ça chez nous parce qu'il y a beaucoup de temps d'attente en fait entre les différents secteurs ouais ok je vois oui quand même du coup parlez moi un peu de ces excels.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
883	9	Christella Umuhoza	32:22	Sur la partie, je vois que là, vous essayez quand même de faire un peu de formules là-dessus, de croiser dans tous les sens, les donner dans tous les sens. Parlez-moi un peu le besoin que vous allez chercher derrière. En fait, parlez- moi des tâches chronophages que vous avez aujourd'hui autour de l'Excel et au-delà de l'Excel. Expliquez-moi un peu en quoi ça vous limite, en quoi ça vous frustre.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
884	9	Clara DI GIROLAMO	32:48	Du coup, je vais parler pour la partie production et pas pour la partie hors de lancement. Nous, en production, la partie chronophage, tous les jours, on va venir mettre à jour des Excel pour venir voir. En fait, en production, on a nos quatre indicateurs, c'est coût, qualité, délai, sécurité. Sécurité, c'est assez facile, on ne travaille pas avec des Excel parce qu'il y a un accident ou il n'y a pas d'accident. Ensuite, on fait de l'amélioration continue et de la prévention dessus, donc ça, on n'en parle pas. Toute la particularité, ça va être les rebuts, donc ça c'est pareil, c'est indépendant de l'informatique. Et ensuite on a vraiment toute la partie du coût, délai et coût.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
885	9	Clara DI GIROLAMO	33:39	La partie délai, alors on va plutôt partir de la partie coût, la partie coût ça va être toute la partie est-ce que je respecte mes temps standards, c'est-à-dire que j'ai un prix, donc un PLI, prix de revient industriel qui est à 10 euros, parce qu'on a calculé que ce produit on le produisait en tout 20 minutes. Si moi en production maintenant je mets 40 minutes pour le produire et bien forcément je vais exploser mes coûts standards parce que j'aurais passé beaucoup trop de temps dessus.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
886	9	Clara DI GIROLAMO	34:08	Donc en fait tous les jours les animatrices et même les responsables de production, on vient chercher dans C-LOB des informations, donc les informations ça va être est-ce que, comme dans toutes les productions, nos opératrices opérateurs se mettent sur les commandes, donc ils vont venir flasher leur temps sur C-LOB, en disant je commence ma commande maintenant, je la termine maintenant, là je fais une pause, etc. Déjà la première chose si on veut que les gens, s'ils travaillent 7h30 dans la journée, normalement je dois avoir 7h30 de flashé dans la journée. Si j'ai quelqu'un qui s'est flashé pendant 5h, ça veut dire que pendant 2h30 il n'était pas flashé, ça veut dire qu'on ne sait pas ce qu'il fait pendant 2h30. Donc ça je vais aller chercher sur Syllab est-ce que les gens se sont bien flashés pendant la journée.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
920	9	Christella Umuhoza	50:33	On regarde et puis on imagine en vraie production, si ce modèle est en production, quel est le coût qu'il va générer au fur et à mesure et puis le balancer avec l'intérêt qu'il y a derrière. S'ils génèrent du coût mais que vous ne gagnez rien en termes de gains de temps ou en termes d'efficacité de comment les ressources fonctionnent vis-à-vis de comment vous les avez placés, peut-être que ça ne valait pas le coup. Donc c'est un peu ça l'aspect, mais oui aujourd'hui les modèles existent. Oui aujourd'hui on peut les mettre en place niveau simple, niveau complexe, Après, c'est une étude à faire. Aujourd'hui, c'est quelque chose qui est un peu lourd pour vous de votre côté?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
887	9	Clara DI GIROLAMO	35:02	Ensuite, je vais regarder les opérations qui sont terminées. Dans CILOB, on me disait un temps standard de 10 minutes. Est-ce que j'ai bien respecté mes 10 minutes ? Oui, non. C'est pareil, on vient chercher dans CILOB toutes les opérations qui ont été terminées aujourd'hui et on vient regarder dans des fichiers, est-ce que j'ai bien mes temps standards qui sont respectés. Ça, je peux vous remontrer sur Syllab comment les animatrices font et ce qui est du coup... Donc en fait, tous les jours, les animatrices, vous voyez, elles ont un indicateur. Donc ça, c'est nous qui l'avons créé. Indicateur jour, avance, retard. Donc par exemple, fin réelle, si je mets la journée d'hier. Ça, c'est mon secteur. Là, vous voyez, j'ai... Bon, alors moi, c'est un petit secteur. Donc j'ai 18 lignes. En tout, en fait, j'ai perdu 1h31.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
888	9	Clara DI GIROLAMO	36:11	Donc en fait, par rapport à mes temps standards, mes opérateurs, ils ont mis 1h30 en plus que ce qu'ils devaient faire. Donc hier, j'ai perdu du temps.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
889	9	Christella Umuhoza	36:21	Oui, quand même.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
890	9	Clara DI GIROLAMO	36:22	Vous voyez, par rapport à ce que je devais faire. Ça, c'est une manipulation que je fais tous les jours. Ensuite, je reviens ici, l'autre ici c'est... Ici tac tac alors bon là moi je le fais de tête parce que c'est assez facile mais en fait j'ai deux opérateurs ils sont... Alors ici c'est lequel ?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
891	9	Christella Umuhoza	37:00	C'Est Soundprod vous êtes ici mais je ne vois pas l'écran oui excusez-moi.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
892	9	Clara DI GIROLAMO	37:07	Je ne vous ai pas partagé l'écran excusez-moi hop bah du coup je vous refais celui derrière moi Donc du coup vous êtes dans le tableau de bord ici sur C-LOG. Donc ça c'est nous qui avons créé tous ces indicateurs. Donc en fait ça c'est une manipulation que je dois faire tous les jours en tant que chef d'équipe. Donc là vous voyez ici, en fait je regarde ici, j'ai somme moins 1h31, ça veut dire qu'hier dans mon équipe j'ai perdu 1h31 par rapport à mes temps standards.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
893	9	Christella Umuhoza	37:48	Il va entendre tout l'équipe, pas vous individuellement, donc tout l'équipe entre les... Oui.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
894	9	Clara DI GIROLAMO	37:55	Alors moi, mon équipe, la partie du bas, ils sont deux, et l'équipe du haut, dans mes secteurs, ça dépend des journées, parfois ils sont deux, trois, quatre, donc je n'ai pas beaucoup de personnes, ça va assez vite à regarder, je n'ai pas beaucoup de clics. Dans les gros secteurs en fabrication, c'est pour ça que Jonathan est vraiment responsable de prod, il a 20 personnes à gérer, donc ça en vaut plus long.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
895	9	Clara DI GIROLAMO	38:12	Mais vous voyez en fait moi je regarde par exemple hier moi à 4h46 sur cette opération ici la personne a perdu 4h46 donc j'avais un temps standard temps travaillé théorique on me demandait de le faire en 10 minutes et il est resté pendant 5h pratiquement dessus donc là moi je vais aller dire à la personne qu'est-ce qui s'est passé en fait pourquoi t'as mis 5h à la place de 10 minutes donc en fait je regarde un petit peu les temps tous les jours comme ça pour voir les gros écarts. Par exemple, quand j'ai une minute en plus, je ne vais pas aller chercher à comprendre ce qui s'est passé pour une minute. Pour l'instant, on n'est pas encore à la limite.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
896	9	Christella Umuhoza	38:51	Ok, répétez pour moi le sondage en termes de temps. Quand est-ce que c'est trop et quand est-ce que c'est acceptable?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
897	9	Clara DI GIROLAMO	39:01	Alors, on va dire que c'est plus ou moins trois heures.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
898	9	Christella Umuhoza	39:07	Donc là c'est dans le temps. Là c'est bon. Une heure et demie c'est ok.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
899	9	Clara DI GIROLAMO	39:12	Si c'est trois heures... Non, c'est pas... Non, c'est... En fait il faut prendre un peu l'historique. Alors moi je ne suis pas là depuis... Je suis là depuis trois jours donc... Et ça on ne l'avait pas quand je suis partie, c'est tout nouveau. Donc j'ai pas l'historique de mes secteurs, mais en fait je sais que par lot, on va regarder les commandes qui sont à moins de 3h ou les commandes qui sont à plus de 3h, on va aller regarder dans le détail ce qui s'est passé. Mais par ligne en fait, pas en tout, par ligne. Donc là moi par exemple, celle qui m'a vraiment manqué, et là où je dois aller voir la personne, c'est celle-ci. Je regarde le 4h46, c'est pas normal.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
900	9	Christella Umuhoza	39:54	D'Accord ok du coup là on est sur la moyenne vous regardez ce qui sort de l'eau et puis vous dites alarmant ok oui voilà très très.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
901	9	Clara DI GIROLAMO	40:05	Clair et donc ça c'est pour les temps et ensuite donc on veut que les personnes soient donc sur les commandes donc du coup ce qu'on fait ici en fait Parce que c'est bien de se dire que le temps était correct, mais si le temps est correct mais que la personne n'était pas sur la commande, ça ne fonctionne pas en fait. Vous voyez, il faut qu'il y ait un équilibre des deux en fait. Il faut que la personne respecte son temps mais qu'elle ait aussi flashé, enregistré sur SILOP quand elle est en train de produire. Parce que je pourrais très bien tricher en me disant je vais signaler sur SILOP que je m'enlève de la commande en disant que j'ai fini, mais en fait je suis encore en train de produire à un côté.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
902	9	Clara DI GIROLAMO	40:50	Donc on a créé un autre indicateur qui s'appelle indicateur jour temps présent sur OEF. Et donc là c'est pareil, je vais venir mettre mon code du secteur. Ça c'est vraiment interne à cousin. Et moi hier, Donc ils sont deux dans mon équipe, donc deux fois 7h30 ils auraient dû être flashés pendant 15h. Hier ils étaient flashés 8h12. Donc j'ai quand même un écart. Donc après je vais aller voir en détail ce qui s'est passé, pourquoi ils n'étaient pas... Pourquoi ils n'étaient pas flashés pendant... Qu'est-ce qui s'est passé ? Pourquoi pendant 15h-8h12 du coup ils n'étaient pas flashés ?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
903	9	Christella Umuhoza	41:28	Donc vous allez faire quoi ? Vous allez demander aux individus ?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
904	9	Clara DI GIROLAMO	41:33	Non, alors en fait, là par contre je ne suis pas assez... Tout le monde s'est rechargé de temps. Alors là, je découvre ça aujourd'hui.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
905	9	Christella Umuhoza	41:47	Du coup, pas de souci. Quand vous aurez les étapes, vous me direz. Dans le cas classique, comment vérifier ? Faites cette vérification. Est-ce que c'est une vérification verbale ou c'est une vérification de croisement entre des détails entrés?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
925	9	Clara DI GIROLAMO	52:38	C'est-à-dire ?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
907	9	Clara DI GIROLAMO	42:30	En fait on enregistre tout, donc par exemple nous on veut être à 72% parce qu'on a également du travail qui s'appelle hors poste, le hors poste ça va être le nettoyage des lignes, ça va être, qu'est-ce qu'il y a comme hors poste, de l'amélioration continue, les étirements, on fait des étirements tous les jours en production, ça va être les pauses etc, donc ça c'est du hors poste, donc on estime que par jour on veut être à 72% de temps travaillé et 28% de temps ça va plus être de la qualité, donc des prélèvements microbiaux, enfin toutes les choses comme ça. Et donc là, vous voyez, on a la tendance, donc on enregistre tout ici et après, en fait, on peut aller voir personne par personne qui était en production, qui était en hors-poste.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
908	9	Clara DI GIROLAMO	43:13	Et en fait, après, SILOB, en fait, nous donne le gros, on va dire. Et nous, derrière, en fait, avec tous nos TCD, on va vraiment venir faire la macro-analyse derrière. Là, je vous montre un petit peu, mais alors attendez, hop, oui, en fait, bilan, analyse hors poste, ici, je peux venir voir, bah, en fait, ici, j'avais, là, je vois, ok, pendant 8h12, ils étaient flashés. Ok, mais maintenant, vraiment, qu'est-ce qui s'est passé dans mon équipe ? Moi, j'ai que deux personnes, c'est facile, mais si vous voyez ici, avec une équipe plus complète, ok, bah, là, je vais aller dans le détail, cette personne ici, pendant, alors là, c'était, Le jour 8, le 16-3 il est un peu bizarre. Je pense que typiquement cette personne ne s'est pas déconnectée.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
909	9	Clara DI GIROLAMO	44:05	Elle ne s'est pas déconnectée tout simplement, mais vous voyez par exemple, si je regarde ici, Nathalie, elle est restée pendant 3h30 en hors poste. Donc bon, Nathalie, qu'est-ce qui s'est passé ? Oui, je faisais un truc pour la qualité. Bon, d'accord. Et en fait, vraiment, on peut aller beaucoup plus dans le détail, du coup, grâce à nos TCD. Mais ça, du coup, c'est chaque jour, on doit venir extraire les données de Syllab vers un Excel. Donc on fait pareil en fait, on fait ça pour les coûts et on va faire ça pour les délais également. Les délais en fait ça va être ok, aujourd'hui j'ai fini tel OEF, tel OEF, demain il me reste ça, ça, ça, comme OEF à faire. Et donc du coup on va revenir mettre un jour tous les jours.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
910	9	Christella Umuhoza	44:56	C'est un travail assez... Qui prend du temps.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
911	9	Clara DI GIROLAMO	45:07	Qui prend du temps, oui, alors, oui, ça prend du... Est-ce que ça prend du temps ? Oui, c'est 10 minutes par jour peut- être. En fait, non. Le mettre à jour et juste sortir les données, ça va assez vite, 7-8 minutes, c'est fait. Après, par contre, si on veut analyser derrière, oui, ça prend plus de temps.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
912	9	Christella Umuhoza	45:26	C'est l'analyse qui prend le temps, ok. Et du coup, vous avez déjà dit Dans mon quotidien, entre ces tâches d'analyse,	interviewer	\N	2025-11-18 13:45:49.042987+00	9
913	9	Clara DI GIROLAMO	46:09	Beaucoup vu mon mari alors je sais pas alors j'ai deux cas de figure je vais vous remettre sur je ne vois pas, c'est bizarre de parler en Excel, hop. Du coup, je regarde un petit peu, moi, l'IFR, lui, il utilise beaucoup pour ses présentations, pour ses musées et pour la traduction anglais-français. Il claque le texte et ça traduit direct, ça prend deux secondes. Pour les présentations, par exemple, faire une affiche de... Tout ce qui va être encouragement des équipes ou autre, ça prend 4 secondes à faire alors qu'avant il fallait passer par PowerPoint ou autre, ça prenait beaucoup de temps, tout ça.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
914	9	Clara DI GIROLAMO	46:49	Et après moi je me posais la question, mais ça je l'avais plus vu dans des usines à l'étranger, mais je ne sais pas si c'est de l'IA, enfin comme vous le faites, ça va plus être par exemple, j'ai 50 heures de personnel, j'ai 70 heures de charge de travail. Dans ces 60 heures de charge de travail, j'en ai, c'est réparti avec autant d'heures par secteur. Après moi j'aimerais bien même aller dans le détail, j'ai mes machines aussi et du coup j'ai des 50 heures de personnel qui sont disponibles, mais parmi ces 50 heures, j'ai 10 heures de personnel qui est capable de faire ça, 10 heures qui est capable de faire ça par rapport aux formations. Est-ce que l'IA est capable de me dire bon bah ok du coup je proposerais de mettre telle personne-là, telle personne-là, telle personne-là.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
915	9	Clara DI GIROLAMO	47:40	Parce que parfois pour nous c'est un peu un casse-tête de se dire, on organise les commandes en fonction des compétences des gens, en fonction du nombre d'heures planifiées par type de secteur ou par type de machine, en fonction des compétences des gens. J'avais prévu mon planning comme ça, oui, sauf qu'aujourd'hui j'ai huit absentes, ce qui est vraiment le cas en ce moment. Est-ce que l'IA est capable de me reproposer, très vite en fait, je clique sur un bouton, je re-rends certaines données, est-ce que l'IA est capable de me dire, finalement si tu le fais de	interviewé	\N	2025-11-18 13:45:49.042987+00	10
916	9	Christella Umuhoza	48:24	Des propositions, c'est toujours de l'analytique.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
917	9	Clara DI GIROLAMO	48:33	C'est.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
918	9	Christella Umuhoza	48:33	Toujours de la prédiction dont il se dit vis-à-vis des données que j'ai. Je pense que la façon de mettre ressource X sur projet Y devrait, je pense que sur projet Y, il faudrait mettre telle ressource sur un certain temps Mais du coup, ça vient toujours de la part des infos que j'ai. Donc, vous avez les infos à disposition et puis il va regarder et faire des suggestions. Du coup, de votre côté, pour valider ce que vous dites, oui, peu, dans quelle mesure, ça, ça dépend des infos que vous avez à jour. Par exemple, ça prend en compte Vous, naturellement, traditionnellement, quel est votre process de décision de mettre une telle ressource sur un tel projet? Comment répartir vos 70 heures entre certaines ressources? Est-ce que c'est niveau expérience? Est-ce que c'est niveau...	interviewer	\N	2025-11-18 13:45:49.042987+00	9
919	9	Christella Umuhoza	49:44	Bref, avoir des règles sur lequel vous basez en faisant ça sans l'IA et puis entraîner l'IA à faire la même chose et faire des prédictions et puis après vous pourrez continuer à valider soit non ce que tu me dis c'est cohérent ou c'est pas cohérent et puis elle va se réentraîner au fur et à mesure et donc du coup par contre il faut que ça vaut le coup donc ça dépend de aujourd'hui vous parlez d'usines à l'étranger Il faut regarder en termes de volumétrie de données, est- ce que c'est un cas d'usage qui est très large ou c'est un cas d'usage moyen ou c'est un cas d'usage où il y a des données limitées parce qu'après, on couple un modèle IA avec la quantité de données qu'il y a vis-à-vis de l'État.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
921	9	Clara DI GIROLAMO	51:27	Je pense que pour l'ensemble du management aujourd'hui, c'est notre travail au final de se dire qu'on a tous ces OF à faire, on a ces personnes-là, ok, comment on s'organise? Et ces personnes-là, elles sont formées à tel, tel process,	interviewé	\N	2025-11-18 13:45:49.042987+00	10
926	9	Christella Umuhoza	52:39	Quand vous dites que cette personne est validée pour ce process et celle-là...	interviewer	\N	2025-11-18 13:45:49.042987+00	9
927	9	Clara DI GIROLAMO	52:42	Elle reçoit une formation et on doit vérifier au fur et à mesure la qualité de ses produits, le temps, et une fois que la qualité et le temps standard match, on peut dire que cette personne est validée et il faut qu'elle en fasse un minimum pour pouvoir être validée, formée à ce process. Et je pense qu'une, alors ça dépend des process, mais une personne peut être validée par exemple pour un process un an ou deux, et au bout deux ans il faut la reformer, refaire un questionnaire de validation.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
928	9	Christella Umuhoza	53:14	Ok d'accord, donc ok, je vois. Donc c'est former, valider, former, valider, et puis après un certain temps former encore.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
929	9	Clara DI GIROLAMO	53:22	C'est ça, et en fait à la fin de la formation, la personne reçoit un questionnaire de validation, en fait avec des questions, et elle doit savoir y répondre.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
930	9	Christella Umuhoza	53:30	Et ça vous utilisez quoi comme outils de formation ?	interviewer	\N	2025-11-18 13:45:49.042987+00	9
931	9	Clara DI GIROLAMO	53:36	Nous, c'est à dire on... Les outils de formation, on a des formatrices qui sont formées, qui sont des opérateurs mais qui ont en plus la qualité de formatrice et qui vont du coup recevoir les nouvelles personnes, les former, leur montrer, donc parfois on a des idées. On montre les procédures également qui sont dans le système qualité. Après, comment on forme une personne ? C'est en faisant pratiquer la personne, bien évidemment. On a des échantillons, des défauts tech. Donc une défaut tech, ça va être en fait dans un classeur, on va récolter, on va avoir plusieurs produits et on va dire, ça c'est un produit qui est conforme, ça c'est un produit qui est non conforme. Donc la nouvelle personne doit savoir où se trouvent les défauts tech, doit savoir identifier les produits conformes, non conformes, ça.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
932	9	Christella Umuhoza	54:27	Va être tout ça. Je vois. Donc c'est entre les vidéos, ce qu'on peut mettre en vidéo, ces documents et puis après il y a bien sûr.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
933	9	Clara DI GIROLAMO	54:38	La... Oui en fait c'est vraiment une partie là. Tout ce qui est formation c'est vraiment humain, ça c'est très humain. Mais après par contre le fait de savoir, par exemple moi je suis nouvelle en production, nouvelle responsable, j'ai mon ensemble du personnel, qui est validé, formé, ça en fait j'ai un classeur Excel et je regarde qui est formé, validé à tout ce process là en fait tout simplement.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
934	9	Christella Umuhoza	55:01	D'accord, ok, donc réallocation des ressources en fait c'est un des cas d'usage que je parlerai. Ouais, en fait c'est un cas d'usage qui pourrait être simple et complexe comme je vous l'ai dit, donc on pourra quand même creuser cette partie. Il faut savoir que le process sur aujourd'hui, c'est qu'aujourd'hui, on fait les entretiens. C'est la phase 2, on fait les entretiens. Après les entretiens, on regarde des synergies entre différents entretiens. On regarde des cohérences. Par exemple, l'Excel est très cohérent dans tous les entretiens que j'ai déjà eu. J'en ai déjà vu d'autres sur différents entretiens en Excel, de marketing à supply à tout le monde. Et à chaque fois qu'on voit beaucoup d'Excel, ça appelle une opportunité d'automatisation, ça dit la volumétrie de data. Ça, par exemple, c'est une synergie.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
935	9	Christella Umuhoza	56:08	Mais on se base sur tous les entretiens pour identifier d'autres synergies ou même des cas d'usages qui peuvent être spécifiques, des challenges qui ressortent dans différentes interviews. Et puis on imagine les ateliers qu'on pourra faire ensemble avec vous. Et donc, le but des ateliers, ils ont des thèmes, ça peut être des thèmes sur la valorisation de la donnée, ça peut être des thèmes sur l'automatisation, ça peut être des thèmes sur l'innovation, sur le workflow, même si je pense que le workflow chez Cousins, c'est très strict, c'est très médical, donc on ne touche pas tellement, mais c'est plutôt dans la façon de travailler, je pense qu'il y aura sa place. Donc, on prend ces ateliers, on imagine ensemble et après, On a quelques cas d'usage sur lesquels on est convaincu que vous pourrez vous investir dans un département ou l'autre.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
936	9	Christella Umuhoza	57:05	Et on fait une roadmap, on la propose et on vous parle de l'utilité de cette roadmap. Et puis voilà, vous décidez sur quelle roadmap vous allez et nous, on peut vous accompagner sur les prochaines étapes de travailler ces cas d'usage, de travailler l'implémentation, de les déployer, commencer à tester et déployer. Je vais vous envoyer le compte rendu de cette réunion et puis je suis sûre que vous aurez des infos dans la foulée sur les prochaines étapes. Ça marche très bien.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
937	9	Clara DI GIROLAMO	57:39	Est-ce que vous, de votre côté, vous avez des exemples d'utilisation de l'IA en industrie un peu similaire à la nôtre ?	interviewé	\N	2025-11-18 13:45:49.042987+00	10
938	9	Christella Umuhoza	57:48	Oui, les cas d'usage que j'ai vu le plus en industrie, alors est-ce que c'est vraiment en industrie, mais par exemple c'est, on a un client qui gère leur capteur, le parc de capteurs, donc ils produisent des capteurs, ils les installent et ils essaient d'analyser les données qui sortent de ces capteurs pour pouvoir se dire On a des défauts sur certains des capteurs que nous avons placés chez ClientAZ et puis ils arrivent à faire de la maintenance prédictive là-dessus. Donc, c'est la production pas sur la chaîne, mais plutôt sur le produit. Ça, vous ne pouvez pas le faire en domaine médical parce que c'est compliqué.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
939	9	Clara DI GIROLAMO	58:33	Ils sont plantés.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
940	9	Christella Umuhoza	58:35	Exactement. Mais en parallèle, plutôt la partie composition des fiches techniques, ça, c'est pas côté production, mais pour certaines industries, ils composent beaucoup de documentation sur les fiches techniques, donc ça	interviewer	\N	2025-11-18 13:45:49.042987+00	9
941	9	Clara DI GIROLAMO	59:37	Bon, merci.	interviewé	\N	2025-11-18 13:45:49.042987+00	10
942	9	Christella Umuhoza	59:38	Eh bien, merci beaucoup. Bon après-midi à vous. Bon après-midi. Merci, au revoir. Au revoir.	interviewer	\N	2025-11-18 13:45:49.042987+00	9
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.users (id, username, email, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: word_extractions; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.word_extractions (id, document_id, extraction_type, data, created_at) FROM stdin;
\.


--
-- Data for Name: workflow_states; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.workflow_states (id, project_id, workflow_type, thread_id, state_data, status, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: workshops; Type: TABLE DATA; Schema: public; Owner: aiko_user
--

COPY public.workshops (id, document_id, atelier_name, raw_extract, aggregate, created_at, updated_at) FROM stdin;
7	10	Direction commerciale	{"use_case1": {"text": "IA qui croise et analyse les données des marché (actuellement excel)", "objective": ""}, "use_case2": {"text": "IA qui assiste les équipes sur les NPS/taux de satisfaction", "objective": ""}, "use_case3": {"text": "Veille marché-données du marché (tout ce qui est d'actualité, ventes, acheteurs)", "objective": "Anticiper et prioriser les marchés? Pour analyser la concurrence"}, "use_case4": {"text": "IA qui cherche en fonction d'uns secteur geo, analyser les clients ses tendance et organise les tournees", "objective": ""}, "use_case5": {"text": "Etablir le bon prix (acceptable ou/et plus élevé) par marché par pays", "objective": "Pricing efficace"}, "use_case6": {"text": "Cousin Academy > automatisation du suivi des formations. Taux de transformatio et taux de fidelisation", "objective": ""}, "use_case7": {"text": "IA qui optimise les plans de tournée pour entretiens et acquisition client", "objective": ""}, "use_case8": {"text": "Définir un budget vente par client (prediction)", "objective": ""}, "use_case9": {"text": "IA qui analyse, alerte sur les chiffres ventes (hausse et baisse) et suggère des actions à faire", "objective": "Aide à la decision vente vis à vis du client"}, "use_case10": {"text": "Liste d'anciens clients-anciens projets- Actuellement PARTOUT (Excel, CEGID)", "objective": "Base d'anciens clients, relancer, repertorier,"}, "use_case11": {"text": "IA predicitif pour identifier les futurs KOLs pour les cibler rapidement", "objective": ""}, "use_case12": {"text": "Identification des decideurs et des societe (profilage) sur perimetre pour gernerer des emails personnalisés avec offre adaptée", "objective": ""}, "use_case13": {"text": "IA qui gère les appels entrants (service client)", "objective": "Améliorer la pertinence du service"}, "use_case14": {"text": "une liste de tout les acteurs qui ont à faire avec nos produits- veille client", "objective": "Se faire une base de clients prospects"}, "use_case15": {"text": "Chiffrage automatique pour des reponses au devis avec un benchmark par rapport au client", "objective": ""}, "use_case16": {"text": "Gestion des appels entrants (telephone, emails) pour un certain niveau de questions et CS", "objective": ""}, "use_case17": {"text": "Yield Management - gestion des prix en fonction des pays", "objective": ""}, "use_case18": {"text": "IA qui analyse les emails, catégorise et propose une réponse", "objective": ""}, "use_case19": {"text": "Analyse par l'IA des followers sur LinkedIn", "objective": ""}, "use_case20": {"text": "Analyse brevet à croiser avec les echeances et les dynamiques de marché", "objective": ""}, "use_case21": {"text": "Analyse du portefeuille client - base de 750 clients - decryptage des temps courts et temps long", "objective": ""}, "use_case22": {"text": "CRM intelligent nourri par les rapports grace au croisement des data. Injection des compte-rendus dans une base pour organiser les informations", "objective": ""}, "use_case23": {"text": "Veille admin automatique pour les douanes", "objective": ""}, "use_case24": {"text": "IA qui detecte des tendances sur les acteurs / clients via des agregats de mots", "objective": ""}, "use_case25": {"text": "IA qui veille et analyse et conseille pour la strategie a l international (reglementaire, analyse des systemes de santé) pour plus d intelligence geo politique", "objective": ""}, "use_case26": {"text": "Automatisation de la collecte des cartes de visite pour entrees des donnees sur le CRM", "objective": ""}, "use_case27": {"text": "Une IA qui permettrait de diffuser de l'information produit dans la langue de l utilisateur pour le vendeur.", "objective": ""}, "use_case28": {"text": "Prix des remboursement par pays", "objective": ""}, "use_case29": {"text": "Offre adaptée vs porte feuille du prospect", "objective": ""}, "use_case30": {"text": "Identifier signaux du marché", "objective": ""}, "use_case31": {"text": "Detection automatique des pratictiens'/influenceurs dans les établissements\\n-vers qui aller en premier (linkedIn, Facebook, tout reseau)", "objective": ""}, "use_case32": {"text": "IA qui gère/suivi d'un accusé de reception de livraison avec le client en direct", "objective": "Fluidifier l'info de livraison par Cousin. donnée qualitative au client"}, "use_case33": {"text": "IA qui automatise la réponse aux AO (la partie admin)", "objective": ""}, "use_case34": {"text": "Data : rassembler toutes les donnees sur les clients des clients (les docteurs qui se forment)", "objective": ""}}	{"theme": "Optimisation de la Direction Commerciale grâce à l'Intelligence Artificielle et à l'Analyse de Données", "use_cases": [{"title": "Optimisation des Données du Marché", "benefits": ["Centralisation des données de marché pour une analyse approfondie.", "Amélioration des stratégies de vente grâce à une veille de la concurrence.", "Réduction des coûts liés à l'analyse manuelle des données dans Excel."], "objective": "Croiser et analyser les données du marché pour anticiper les tendances et optimiser les décisions commerciales.", "iteration_count": 4}, {"title": "Analyse Prédictive des Taux de Satisfaction", "benefits": ["Identification rapide des points de douleur grâce à l'analyse des NPS.", "Mise en œuvre de mesures correctives basées sur des données réelles.", "Renforcement de la fidélisation des clients par une meilleure satisfaction."], "objective": "Assurer une assistance aux équipes sur les NPS et les taux de satisfaction pour améliorer l'expérience client.", "iteration_count": 2}, {"title": "Automatisation des Plans de Tournée", "benefits": ["Gain de temps et d'efficacité dans la planification des visites clients.", "Maximisation des opportunités commerciales grâce à une meilleure gestion des visites.", "Personnalisation des interactions client en fonction des données analysées."], "objective": "Utiliser l'IA pour optimiser les tournées des équipes commerciales en fonction des analyses de données clients.", "iteration_count": 3}, {"title": "Pricing Dynamique par Marché", "benefits": ["Augmentation de la compétitivité grâce à une stratégie de prix ajustée.", "Amélioration des marges bénéficiaires grâce à une tarification intelligente.", "Réduction des risques liés aux erreurs de pricing."], "objective": "Définir un bon prix par marché et par pays pour maximiser les bénéfices.", "iteration_count": 2}, {"title": "Analyse des Tendances Clients et KOLs", "benefits": ["Accélération du processus de ciblage grâce à l'analyse prédictive.", "Augmentation de l'efficacité des campagnes marketing et commerciales.", "Meilleure anticipation des besoins du marché."], "objective": "Identifier proactivement les KOLs et les tendances dans le secteur pour cibler efficacement les actions commerciales.", "iteration_count": 2}, {"title": "Gestion Automatisée des Appels et Emails", "benefits": ["Amélioration de la rapidité de réponse aux demandes clients.", "Réduction des coûts opérationnels grâce à l'automatisation.", "Amélioration de l'expérience client par une communication fluide."], "objective": "Utiliser l'IA pour gérer efficacement les appels entrants et les demandes par email.", "iteration_count": 3}, {"title": "Intelligence CRM et Collecte de Données", "benefits": ["Centralisation des informations clients pour un accès facilité.", "Amélioration de la prise de décision stratégique grâce à des données précises.", "Augmentation de la réactivité face aux demandes clients."], "objective": "Développer un CRM intelligent alimenté par des données consolidées pour une meilleure gestion client.", "iteration_count": 2}, {"title": "Détection Automatique des Signaux Marché", "benefits": ["Amélioration de la capacité d'adaptation aux fluctuations du marché.", "Accélération de la prise de décision stratégique.", "Développement de produits/services adaptés aux nouvelles tendances."], "objective": "Utiliser l'IA pour identifier les signaux du marché et anticiper les tendances.", "iteration_count": 2}, {"title": "Veille Réglementaire et Stratégique", "benefits": ["Anticipation des différentes réglementations sur les marchés cibles.", "Support dans l'élaboration de stratégies globales basées sur des données fiables.", "Diminution des risques liés aux erreurs réglementaires."], "objective": "Mettre en place une IA pour analyser les données réglementaires et stratégiques à l'international.", "iteration_count": 2}], "workshop_id": "W001"}	2025-11-18 13:45:58.07476+00	2025-11-18 13:47:38.824692+00
8	10	Excellence Opérationnelle	{"use_case1": {"text": "detecter et analyser les relevés de controle de chaque process MSP", "objective": "Moins de tests sur les relevés conformes"}, "use_case2": {"text": "Modification en masse de fichiers excl et word (500 fichiers)", "objective": ""}, "use_case3": {"text": "Extraction auto des données de production ou composant pour faire des calculs analyse du cycle de vie pour impact environmental", "objective": "`Bilan carbone par produit"}, "use_case4": {"text": "Traduction des notices et etiquettes, plaquette, documents.", "objective": "Tout passer en relecture au lieu de faire de la traduction"}, "use_case5": {"text": "Traduction de notices et etiquettes", "objective": "Gain 0.3 etp"}, "use_case6": {"text": "Mise à jour et analyse des temps des donnees techniques de production vs donnees standard", "objective": "entre 2 et 10% de productivité ?"}, "use_case7": {"text": "Contrôle ds dossiers de lots (40h/semaine)", "objective": "Gain de temps/productivité"}, "use_case8": {"text": "Scanner un dossier de lots pour detecter les erreurs dedans", "objective": ""}, "use_case9": {"text": "Gestion des plans d experience / validation / echantillonage, analyse de situation statistique et complexe", "objective": "Gain de temps"}, "use_case10": {"text": "Mettre a jour le fichier de projection de stock automatiquement + analyse + relance des Ordre de Fabrication pour les besoins", "objective": ""}, "use_case11": {"text": "Analyse des logs", "objective": "Remontee des problematiques"}, "use_case12": {"text": "Automatisation de controle de presence des particules de defaut, analyse des soudures sur les sachets (computer vision)", "objective": ""}, "use_case13": {"text": "Analyse des ecarts de stock", "objective": ""}, "use_case14": {"text": "Gestion des historiques - FRC fiche de reclamation client pour gerer les PMS Post Market Surveillance.", "objective": ""}, "use_case15": {"text": "Minimum de composants = commande automatique. passage de commande automatiquement pour certains composants", "objective": "etre pro actif"}, "use_case16": {"text": "Aide au recrutement pour la prod, rédaction fiche de poste", "objective": "Gain de temps et pertinence en recrutement"}, "use_case17": {"text": "Generateur automatique de flow chart (bcp de documents sont convertis)", "objective": "Standardiser la generation et gagner du temps"}, "use_case18": {"text": "Compte-rendu synthetique des reunions.", "objective": ""}, "use_case19": {"text": "Maintenance predictive sur les Central de traitement d Air (CTA)", "objective": "Ameliorer la consommation d'é\\\\nergie et détecter la dérive"}, "use_case20": {"text": "Controle des tricots et des dessins de tricotage par computer vision.", "objective": "Detecter en ligne des defauts en continue"}, "use_case21": {"text": "Attribution automatique des roles pour les serveurs et des acces", "objective": ""}, "use_case22": {"text": "Mettre a jour les commandes avec les delais de livraison sur la base des Accusés de reception", "objective": ""}, "use_case23": {"text": "Compilation des informations auto pour les dossierd de sous traitance", "objective": ""}, "use_case24": {"text": "Achat de composant - Rapprochement automatique des factures avec les bons de livraison", "objective": ""}, "use_case25": {"text": "Saisie et analyse de la base MSP", "objective": ""}, "use_case26": {"text": "Plateforme automatique d'enregistrement des tickets et reponse automatique", "objective": "Gain de temps 1H par jour"}, "use_case27": {"text": "Analyse des donnees de scellage, parametres machine", "objective": "analyse des tendances process"}, "use_case28": {"text": "Verification des etiquettes en cours de production pour verifier la conformité (computer vision)", "objective": ""}, "use_case29": {"text": "Design et analyse d un plan d experience complexe (faire les tests pour definir le process optimal de fabrication)", "objective": ""}, "use_case30": {"text": "Suivi Enegertique", "objective": "Gain et optimisation énergetique"}, "use_case31": {"text": "Redaction des Change Request - evaluation des changements. Historique disponible", "objective": ""}, "use_case32": {"text": "Reconnaissance visuelle analyse d image des contrôles d'entrées dans la warehouse", "objective": "acceleration du flux"}, "use_case33": {"text": "Analyse du comportement des machines (IT) pour prevenir les cyber attaqques", "objective": ""}, "use_case34": {"text": "ChatGPT interne avec acces à la GED QI QO QP pour repondre aux questions techniques", "objective": ""}, "use_case35": {"text": "Avoir des propositions d'appro en fonction de l etat des stocks, les delais de livraisons et l estimation des ventes.\\n\\nPDP à 4 semaines", "objective": ""}, "use_case36": {"text": "Synthetiser et rechercher des informations sur plusieurs documents en un document propre QI QO QP", "objective": ""}, "use_case37": {"text": "automatisation des documents (word ou excl) de sous traitance et de conception", "objective": "standardiser et gagner du temps"}, "use_case38": {"text": "Mise a jour des serveurs ou postes", "objective": "Gagner 0.25 ETP"}, "use_case39": {"text": "Aide au recrutement TeamTailor. (Deploiement d un ATS)", "objective": ""}, "use_case40": {"text": "Optimisation et selection des frais generaux assistance a la selection des prestataires", "objective": ""}, "use_case41": {"text": "PLateforme de mise a jour automatique des mots de passe", "objective": "Gain de temps"}, "use_case42": {"text": "Sortir les plaquettes marketing - fiche produi en automatique", "objective": ""}, "use_case43": {"text": "Mise à jour des KPIs en prod (2h/j)", "objective": "Suivi BI"}, "use_case44": {"text": "Bloquer la prod en cas de controle Non conforme et extraire les cas precedents pour savoir comment agir (recherche de l historique)", "objective": "autonomiser la production"}}	{"theme": "Excellence Opérationnelle", "use_cases": [{"title": "Automatisation de l'extraction et analyse des données de production", "benefits": ["Diminution des erreurs humaines lors de l'extraction des données", "Accélération des processus d'analyse environnementale", "Amélioration de la conformité réglementaire en matière d'impact environnemental"], "objective": "Effectuer une extraction automatique des données de production pour réaliser une analyse du cycle de vie visant à évaluer l'impact environnemental, notamment le bilan carbone par produit.", "iteration_count": 1}, {"title": "Contrôle et mise à jour des dossiers de lots", "benefits": ["Gain de temps significatif dans le contrôle des dossiers", "Amélioration de la qualité des données grâce à la détection précoce des erreurs", "Réduction du temps dédié au traitement des erreurs"], "objective": "Automatiser le contrôle des dossiers de lots et scanner les documents pour détecter les erreurs.", "iteration_count": 2}, {"title": "Optimisation de la gestion des traductions", "benefits": ["Réduction des coûts liés à la traduction", "Amélioration de la qualité et de la conformité des documents traduits", "Gain de 0,3 ETP en ressources humaines"], "objective": "Mettre en place un processus automatisé de traduction des notices et étiquettes, avec relecture systématique.", "iteration_count": 2}, {"title": "Mise à jour automatique des fichiers d'exclusion et création de documents", "benefits": ["Gain de temps significatif lors de la mise à jour de documents", "Réduction des erreurs liées aux mises à jour manuelles", "Standardisation des documents générés"], "objective": "Automatisation de la mise à jour en masse de fichiers Word et Excel pour simplifier la création et la gestion de documents.", "iteration_count": 1}, {"title": "Suivi et optimisation de la performance énergétique", "benefits": ["Amélioration de l'efficacité énergétique", "Prévention des pannes et minimisation des coûts de maintenance", "Réduction de l'empreinte carbone de l'entreprise"], "objective": "Implémentation d'un système de maintenance prédictive sur les centrales de traitement d'air pour optimiser la consommation d'énergie.", "iteration_count": 1}, {"title": "Automatisation des commandes de composants", "benefits": ["Proactivité dans la gestion des approvisionnements", "Réduction des ruptures de stocks", "Optimisation des coûts de stockage"], "objective": "Mise en place d'un système de commande automatique pour les composants en fonction de l'état des stocks et des prévisions de ventes.", "iteration_count": 1}, {"title": "Rapprochement automatique des factures et bons de livraison", "benefits": ["Gain de temps lors du traitement des factures", "Réduction des erreurs de comptabilité", "Amélioration de la transparence financière"], "objective": "Automatiser le rapprochement des factures d'achat avec les bons de livraison pour simplifier le processus comptable.", "iteration_count": 1}, {"title": "Analyse des écarts de stock et optimisation", "benefits": ["Amélioration de l'exactitude des stocks", "Réduction des coûts liés aux surstocks ou aux ruptures", "Optimisation des processus de gestion des stocks"], "objective": "Analyser les écarts de stock pour identifier et corriger les problèmes d'inventaire.", "iteration_count": 1}, {"title": "Gestion des rapports et des historiques pour la conformité", "benefits": ["Facilitation des audits grâce à une documentation claire", "Amélioration de la réactivité face aux changements", "Meilleure gestion des réclamations clients"], "objective": "Évaluer et documenter les changements via des Change Requests pour une meilleure traçabilité.", "iteration_count": 1}, {"title": "Mise à jour automatique des KPIs de production", "benefits": ["Suivi en temps réel de la performance de production", "Facilitation de la prise de décision basée sur des données actualisées", "Gain de 2 heures par jour en gestion des données"], "objective": "Implémentation d’un système de mise à jour automatique des indicateurs de performance clés (KPIs) en production.", "iteration_count": 1}], "workshop_id": "W002"}	2025-11-18 13:45:58.07476+00	2025-11-18 13:47:54.221684+00
9	10	Formation, Capital des données	{"use_case1": {"text": "suivi de carrière en fonction de son historique, ses compétences, plan de formation disponibles sur le marché - quelles sont les formations disponibles sur quelle thématique", "objective": "plan de progression d'un collaborateur"}, "use_case2": {"text": "Regrouper toutes les données marché faite par les gens-collaborateurs (FT, historique) pour en faire une analyse des données marché", "objective": "Mieux connaitre les données marché"}, "use_case3": {"text": "Génération de CR automatique quelque soit le nature de l'échange (format divers)", "objective": "Gain de temps"}, "use_case4": {"text": "Réaliser questionnaires de validation des connaissances  (transverse aux différents services)", "objective": "Capitaliser sur la connaissance"}, "use_case5": {"text": "historique des études pour aider à la rédaction du protocole (veille documentaire), synthèse de l'existant dans la littérature de nos concurrents et/ou produits similaires", "objective": "rédaction d'un protocole d'étude"}, "use_case6": {"text": "screen des CV pour optimiser le temps passé à la lecture des CV alimenté de notre base - mise à jour des fiches de postes pour attirer les bons profils", "objective": "Cibler les bons candidats pour le poste"}, "use_case7": {"text": "Automatiser les mise à jour des docs procédures (versioning-Tableaux Excel)/ Gap Analysis", "objective": "Mise à jour des pages"}, "use_case8": {"text": "Ajustement de la fréquence de test microbio - Suivi long terme microbio en fonction des résultats internes ou de la sensibilité de la matière 1ere", "objective": "Ajuster la fréquence des tests micro-bio"}, "use_case9": {"text": "Génération de rapport PMS (marketing) et PSUR (reglementaire)", "objective": "Gain de temps ++ car beaucoup d'éléments à consolider"}, "use_case10": {"text": "Réaliser des MAJ des questionnaires auto dès que les procédures sont MAJ", "objective": "Optimisation formation"}, "use_case11": {"text": "base de données articles avec tous les mots clefs: long de discerner ceux qui ont un impact facteur intéressant -> avec une IA on pourrait faire un screening des 4/5 articles pertinents à lire en priorité // push d'articles 1x/semaine par exemple avec la pertinence/ informations concurrents", "objective": "Veille scientifique et clinique"}, "use_case12": {"text": "Récupérer les évènements, les compte rendu de meeting, les compte rendu d'opération(salons, interviews clients). Etre capable d'intérogger un système qui nous dit ce qui existe ou pas (GED)", "objective": "Gain de temps, récupération des bonnes infos"}, "use_case13": {"text": "Réaliser des animations pour des supports marketing (mettre en mouvement un objet)", "objective": "Gain de temps"}, "use_case14": {"text": "Réaliser des traductions auto de supports audio (associé avec génération support formation associé / CR ...)", "objective": "Gain de temps"}, "use_case15": {"text": "Excellence operationnelle- Qualité--> Logistic\\nIA qui aide à la capture d'info papier(scan?) vers le logistic une fois libéré", "objective": "Gain de temps---beaucoup de temps pour noter"}, "use_case16": {"text": "Outil pour créer un film de formation à partir de différent témoignages, film d'interview, formation d'anatomie, chirurgies...", "objective": "Plusieurs milliers d'euros"}, "use_case17": {"text": "avoir un meilleur offboarding des collaborateurs : quelles données garder en interne // assurer la bonne image de la société", "objective": "aider à l'off boarding des collaborateurs"}, "use_case18": {"text": "IA qui analyse les rapports d'audit et retour de dossier technique (marquage CE, ON) pour extraire les actions à faire par service", "objective": "Aide à la lecture rapide car beaucoup de docs à vérifier, respects des actions"}, "use_case19": {"text": "rédiger des CRV de réunions synthétiques: entretiens de salons//", "objective": "synthétiser"}, "use_case20": {"text": "Automatiser la récupération de données de produits sur les sites des fabriquants à partir d'une liste de produit et / ou de fabriquants", "objective": "Gain de temps et optimisation car actuellement 3 jours par récolte de données"}, "use_case21": {"text": "Faire le gap analysis entre 2 normes suite à mise à jour", "objective": "Gain de temps"}, "use_case22": {"text": "Génération d'image pour insérer dans support marketing (outil firefly de photoshop)", "objective": "Génération image"}, "use_case23": {"text": "Clinique- Rapport reglementaire club Hernie", "objective": "Gain de temps"}, "use_case24": {"text": "Capitaliser l'historique des données de gestion de projet pour proposer des plannings types / matrice de risques lors du démarrage d'un projet (en fonction de sa typologie -> type de produits, marché...)", "objective": "Optimiser démarrage projet"}, "use_case25": {"text": "Formation sur la fabrication produits (video, montage) tout les 1an-2ans--> Connaissance interne", "objective": "Structurer les films, contenu"}, "use_case26": {"text": "Remplir les contrats et saisie automatisées de certains infos pour remplir les champs ( contrat qualité, commerciaux, etc...)", "objective": "Mettre à jour les données, gain de temps"}, "use_case27": {"text": "Analyse des données cliniques pour en faire un argumentaire pour formation et brochure marketing", "objective": "Simplifier création support marketing"}, "use_case28": {"text": "Faire une base de connaissance avec tous les dossiers techniques pour ensuite avec un chatbot interroger le système", "objective": "Gain de temps"}, "use_case29": {"text": "quels sont les organismes qui proposent des sujets précis et particuliers - les identifier - qui proposent les sujets + les organismes adaptés", "objective": "lister les organismes de formation"}}	{"theme": "Optimisation de la gestion des connaissances et des processus internes par l'automatisation et l'analyse des données", "use_cases": [{"title": "Suivi de carrière et plan de formation personnalisé", "benefits": ["Améliorer la satisfaction et la rétention des employés", "Avoir une visibilité claire sur les étapes de développement de carrière", "Optimiser les investissements en formation"], "objective": "Mettre en place un suivi de carrière basé sur l'historique et les compétences des collaborateurs pour identifier les formations disponibles sur le marché et établir un plan de progression.", "iteration_count": 1}, {"title": "Analyse des données de marché", "benefits": ["Obtenir une vision globale et actualisée des tendances du marché", "Aider à la prise de décision stratégique pour le développement des compétences", "Renforcer l'adéquation entre les formations proposées et les attentes du marché"], "objective": "Consolider les données marché provenant des collaborateurs (FT et historique) pour réaliser une analyse approfondie des tendances et des besoins de formation.", "iteration_count": 1}, {"title": "Automatisation de la génération de comptes-rendus", "benefits": ["Gain de temps significatif pour le personnel", "Amélioration de la traçabilité des échanges", "Standardisation des comptes-rendus"], "objective": "Développer un système pour générer automatiquement des comptes-rendus indépendamment de la nature de l’échange, afin de réduire le temps passé sur cette tâche.", "iteration_count": 1}, {"title": "Validation des connaissances à travers des questionnaires", "benefits": ["Assurer la montée en compétences des équipes", "Identifier les lacunes en matière de connaissances", "Favoriser l'apprentissage continu"], "objective": "Réaliser des questionnaires de validation des connaissances afin de capitaliser sur l'expertise au sein des différents services.", "iteration_count": 1}, {"title": "Synthèse documentaire pour rédaction de protocoles", "benefits": ["Faciliter la recherche d'informations pertinentes", "Accélérer le processus de rédaction des protocoles", "Améliorer la qualité de la documentation"], "objective": "Établir un historique des études et une synthèse des documents et littérature concurrentielle pour faciliter la rédaction de protocoles d'études.", "iteration_count": 1}, {"title": "Optimisation du screening des CV", "benefits": ["Cibler efficacement les bons profils", "Réduire le temps passé par les recruteurs", "Améliorer la qualité des recrutements"], "objective": "Mettre en place un outil de screening de CV pour optimiser la sélection des candidats et mettre à jour les fiches de postes selon les besoins.", "iteration_count": 1}, {"title": "Mise à jour automatique des documents de procédures", "benefits": ["Réduction des erreurs dues à une information obsolète", "Gain de temps substantiel lors des mises à jour", "Amélioration de l'efficacité opérationnelle"], "objective": "Automatiser les mises à jour des documents de procédures pour garantir que les informations sont toujours à jour et conformes.", "iteration_count": 1}, {"title": "Ajustement des fréquences de tests microbiologiques", "benefits": ["Amélioration de la gestion des risques", "Optimisation de la planification des tests", "Renforcement de la conformité réglementaire"], "objective": "Ajuster et suivre la fréquence des tests microbiologiques sur la base des résultats internes ou de la sensibilité des matières premières.", "iteration_count": 1}, {"title": "Génération de rapports PMS et PSUR", "benefits": ["Réduire le temps nécessaire pour la préparation des rapports", "Améliorer la conformité des documents", "Libérer des ressources pour des tâches à valeur ajoutée"], "objective": "Mettre en place un système pour générer automatiquement des rapports PMS (Post-Market Surveillance) et des PSUR (Periodic Safety Update Reports) afin de gagner significativement du temps.", "iteration_count": 1}, {"title": "Mise à jour des questionnaires en fonction des procédures", "benefits": ["Optimisation des processus de formation", "Réduction des incohérences entre procédures et formations", "Gain de temps et efficacité accrue"], "objective": "Automatiser les mises à jour des questionnaires auto pour garantir qu'ils soient en accord avec les procédures les plus récentes.", "iteration_count": 1}, {"title": "Veille scientifique et clinique via une base de données", "benefits": ["Accélérer l'accès à l'information critique", "Soutenir la prise de décision basée sur des données factuelles", "Améliorer la pertinence des connaissances partagées"], "objective": "Créer une base de données d’articles scientifiques avec des mots-clés pertinents, permettant d'identifier et de sélectionner rapidement les articles impactants.", "iteration_count": 1}, {"title": "Gestion électronique des documents de réunion et événements", "benefits": ["Amélioration de la visibilité des informations capturées", "Gain de temps grâce à une recherche simplifiée", "Amélioration de la gestion des connaissances"], "objective": "Récupérer les événements et comptes-rendus de meetings pour faciliter l'accès et la consultation des informations importantes.", "iteration_count": 1}, {"title": "Création de supports marketing animés", "benefits": ["Rendre les supports plus attractifs", "Améliorer l'impact visuel des campagnes marketing", "Renforcer l'identité de marque"], "objective": "Réaliser des animations pour rendre les supports marketing plus engageants et dynamiques.", "iteration_count": 1}, {"title": "Automatisation des traductions de supports audio", "benefits": ["Réduction des délais de traduction", "Amélioration de l'accessibilité des supports de formation", "Gain de temps pour les formateurs"], "objective": "Implémenter un système de traduction automatique des supports audio tout en générant les supports de formation associés.", "iteration_count": 1}, {"title": "Capture d'information papier vers solutions logistiques", "benefits": ["Éliminer les tâches manuelles répétitives", "Optimiser le traitement des informations", "Améliorer la réactivité logistique"], "objective": "Mettre en place un système pour scanner et intégrer les documents papier dans les flux logistiques pour une traçabilité améliorée.", "iteration_count": 1}, {"title": "Création de contenu vidéo de formation", "benefits": ["Fournir une documentation visuelle enrichissante", "Accroître l'efficacité des formations", "Améliorer la rétention d'informations"], "objective": "Utiliser une plateforme pour créer des vidéos de formation à partir de témoignages et contenus cliniques.", "iteration_count": 1}, {"title": "Optimisation de l'offboarding des collaborateurs", "benefits": ["Réduction des risques d'oubli d'informations importantes", "Préservation de la culture et de l'image de l'entreprise", "Faciliter la transition et le passage de relais"], "objective": "Développer un processus structuré pour gérer l'offboarding des collaborateurs, en préservant les données essentielles et l'image de l'entreprise.", "iteration_count": 1}, {"title": "Analyse des rapports d'audit pour actions correctives", "benefits": ["Accélérer le processus d'analyse de documents", "Assurer le respect des normes et actions correctives", "Améliorer l'efficacité des audits"], "objective": "Développer une IA capable d'analyser les rapports d'audit et de déterminer les actions correctives nécessaires par service.", "iteration_count": 1}, {"title": "Rédaction de comptes-rendus synthétiques", "benefits": ["Faciliter la compréhension des décisions prises", "Accélérer la diffusion des informations", "Améliorer la productivité des équipes"], "objective": "Établir un format standard pour la rédaction de comptes-rendus de réunions afin d’améliorer la clarté et la cohérence des communications.", "iteration_count": 1}, {"title": "Automatisation de la récupération de données produits", "benefits": ["Réduction significative du temps de travail", "Amélioration de l'exactitude des informations récoltées", "Libération de ressources pour d'autres tâches"], "objective": "Développer un outil pour automatiser la collecte de données sur les produits à partir des sites des fabricants afin de réduire le temps de collecte.", "iteration_count": 1}, {"title": "Analyse des écarts entre normes", "benefits": ["Assurer une mise à jour conforme rapidement", "Soutenir les équipes dans la gestion des compliance", "Améliorer la réactivité aux changements de normes"], "objective": "Faire une analyse des écarts entre deux normes suite à des mises à jour pour garantir la conformité et l'alignement des processus.", "iteration_count": 1}, {"title": "Génération d'images pour supports marketing", "benefits": ["Améliorer l'impact visuel des campagnes", "Réduire le coût de création visuelle", "Accélérer le processus de création de contenu marketing"], "objective": "Mettre en œuvre un outil performant pour générer des images à intégrer dans les supports marketing.", "iteration_count": 1}, {"title": "Rapport réglementaire sur le club Hernie", "benefits": ["Amélioration de la conformité opérationnelle", "Optimisation des ressources nécessaires à la production de rapports", "Renforcement de l’efficacité des opérations"], "objective": "Réaliser un rapport clinique réglementaire pour le club Hernie, assurant conformité et mise à jour des informations.", "iteration_count": 1}, {"title": "Capitalisation des données de gestion de projet", "benefits": ["Améliorer la prévisibilité des projets", "Réduire les erreurs liées à l'inexpérience", "Favoriser un démarrage de projet structuré et efficace"], "objective": "Capitaliser sur l'historique des projets pour établir des plannings types et une matrice de risques lors du démarrage.", "iteration_count": 1}, {"title": "Structuration des formations sur la fabrication des produits", "benefits": ["Assurer une montée en compétences continue des équipes", "Optimiser les processus de fabrication", "Réduction des risques d'erreurs humaines"], "objective": "Organiser les formations sur la fabrication des produits à un intervalle régulier pour maintenir le niveau de compétences.", "iteration_count": 1}, {"title": "Automatisation de la saisie d'informations sur les contrats", "benefits": ["Réduction des erreurs de saisie", "Gain de temps pour les équipes administratives", "Accélération du processus de mise en conformité"], "objective": "Sauter les étapes manuelles en automatisant la saisie d'informations récurrentes sur les contrats de qualité et commerciaux.", "iteration_count": 1}, {"title": "Analyse des données cliniques pour argumentaires", "benefits": ["Rendre les supports plus pertinents et informés", "Accroître l'efficacité des équipes marketing", "Améliorer la qualité générale de la communication externe"], "objective": "Analyser les données cliniques et les synthétiser pour créer des argumentaires adaptés aux supports marketing.", "iteration_count": 1}, {"title": "Création d'une base de connaissances avec chatbot", "benefits": ["Faciliter l'accès à l'information", "Améliorer le service clients/support", "Réduire le temps de recherche d'informations"], "objective": "Établir une base de connaissances incluant tous les dossiers techniques pour permettre une interrogation aisée via un chatbot.", "iteration_count": 1}, {"title": "Répertoire des organismes de formation spécialisés", "benefits": ["Faciliter l'accès à des formations ciblées", "Améliorer la pertinence des choix de formation", "Soutenir la montée en compétences des équipes"], "objective": "Lister les organismes qui proposent des sujets spécifiques et adaptés aux besoins des collaborateurs.", "iteration_count": 1}], "workshop_id": "W003"}	2025-11-18 13:45:58.07476+00	2025-11-18 13:48:17.299531+00
\.


--
-- Name: agent_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.agent_results_id_seq', 12, true);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.documents_id_seq', 10, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.projects_id_seq', 6, true);


--
-- Name: speakers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.speakers_id_seq', 10, true);


--
-- Name: transcripts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.transcripts_id_seq', 942, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: word_extractions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.word_extractions_id_seq', 1, false);


--
-- Name: workflow_states_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.workflow_states_id_seq', 1, false);


--
-- Name: workshops_id_seq; Type: SEQUENCE SET; Schema: public; Owner: aiko_user
--

SELECT pg_catalog.setval('public.workshops_id_seq', 9, true);


--
-- Name: agent_results agent_results_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.agent_results
    ADD CONSTRAINT agent_results_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: projects projects_company_name_key; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_company_name_key UNIQUE (company_name);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: speakers speakers_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT speakers_pkey PRIMARY KEY (id);


--
-- Name: transcripts transcripts_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.transcripts
    ADD CONSTRAINT transcripts_pkey PRIMARY KEY (id);


--
-- Name: speakers uq_speakers_project_name; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT uq_speakers_project_name UNIQUE (project_id, name);


--
-- Name: workflow_states uq_workflow_states_project_workflow_thread; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workflow_states
    ADD CONSTRAINT uq_workflow_states_project_workflow_thread UNIQUE (project_id, workflow_type, thread_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: word_extractions word_extractions_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.word_extractions
    ADD CONSTRAINT word_extractions_pkey PRIMARY KEY (id);


--
-- Name: workflow_states workflow_states_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workflow_states
    ADD CONSTRAINT workflow_states_pkey PRIMARY KEY (id);


--
-- Name: workshops workshops_pkey; Type: CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_pkey PRIMARY KEY (id);


--
-- Name: idx_speakers_project_id; Type: INDEX; Schema: public; Owner: aiko_user
--

CREATE INDEX idx_speakers_project_id ON public.speakers USING btree (project_id);


--
-- Name: idx_speakers_project_type; Type: INDEX; Schema: public; Owner: aiko_user
--

CREATE INDEX idx_speakers_project_type ON public.speakers USING btree (project_id, speaker_type);


--
-- Name: idx_speakers_speaker_type; Type: INDEX; Schema: public; Owner: aiko_user
--

CREATE INDEX idx_speakers_speaker_type ON public.speakers USING btree (speaker_type);


--
-- Name: idx_transcripts_speaker_id; Type: INDEX; Schema: public; Owner: aiko_user
--

CREATE INDEX idx_transcripts_speaker_id ON public.transcripts USING btree (speaker_id);


--
-- Name: agent_results agent_results_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.agent_results
    ADD CONSTRAINT agent_results_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: documents documents_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: transcripts fk_transcripts_speaker_id; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.transcripts
    ADD CONSTRAINT fk_transcripts_speaker_id FOREIGN KEY (speaker_id) REFERENCES public.speakers(id) ON DELETE SET NULL;


--
-- Name: speakers speakers_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.speakers
    ADD CONSTRAINT speakers_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: transcripts transcripts_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.transcripts
    ADD CONSTRAINT transcripts_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: word_extractions word_extractions_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.word_extractions
    ADD CONSTRAINT word_extractions_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: workflow_states workflow_states_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workflow_states
    ADD CONSTRAINT workflow_states_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: workshops workshops_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: aiko_user
--

ALTER TABLE ONLY public.workshops
    ADD CONSTRAINT workshops_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict c4T7L9VanJfnQxtWyK0QqsijRRqCYm1V02VHTK2Vw1CoVhwCgLJjhKNrdsBy4mo

