import React, { useEffect, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import {
  createUserWithEmailAndPassword,
  EmailAuthProvider,
  deleteUser,
  onAuthStateChanged,
  reauthenticateWithCredential,
  reauthenticateWithPopup,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  type User as FirebaseUser,
} from 'firebase/auth';
import { deleteDoc, doc, getDoc, serverTimestamp, setDoc } from 'firebase/firestore';
import {
  ArrowRight, Compass, MapPin, Users, Sparkles, ShieldCheck, Globe2,
  Mountain, Waves, Camera, Utensils, TreePine, Building2, Heart,
  LogOut, UserRound, Check, LoaderCircle, Mail,
  ArrowLeft, Trash2, Plane, SlidersHorizontal,
} from 'lucide-react';
import {
  auth, db, googleProvider, appleProvider, firebaseConfigured,
} from './firebase';
import './styles.css';

type Profile = {
  displayName: string;
  email: string;
  photoURL: string;
  bio: string;
  homeCity: string;
  country: string;
  interests: string[];
  preferredDestinations: string[];
  travelStyle: string;
  budgetRange: string;
  travelPace: string;
  onboardingCompleted: boolean;
};

type Screen = 'home' | 'auth' | 'onboarding' | 'dashboard' | 'profile';
type AuthMode = 'login' | 'register';

const interests = [
  { label: 'Adventure', icon: Mountain }, { label: 'Beaches', icon: Waves },
  { label: 'Photography', icon: Camera }, { label: 'Food', icon: Utensils },
  { label: 'Nature', icon: TreePine }, { label: 'Culture', icon: Building2 },
];
const destinations = ['Goa', 'Jaipur', 'Munnar', 'Rishikesh', 'Hampi', 'Manali', 'Coorg', 'Meghalaya', 'Ladakh', 'Kerala'];
const blankProfile = (user: FirebaseUser): Profile => ({
  displayName: user.displayName || '', email: user.email || '', photoURL: user.photoURL || '',
  bio: '', homeCity: '', country: 'India', interests: [], preferredDestinations: [],
  travelStyle: 'Group travel', budgetRange: 'Mid-range', travelPace: 'Balanced',
  onboardingCompleted: false,
});

function App() {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [screen, setScreen] = useState<Screen>('home');
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [verificationUser, setVerificationUser] = useState<FirebaseUser | null>(null);

  useEffect(() => {
    const currentAuth = auth;
    const firestore = db;
    if (!currentAuth || !firestore) { setLoading(false); return; }
    const unsubscribe = onAuthStateChanged(currentAuth, async (nextUser) => {
      setUser(nextUser);
      setError('');
      if (!nextUser) {
        setProfile(null); setVerificationUser(null); setScreen('home'); setLoading(false); return;
      }
      if (!nextUser.emailVerified && nextUser.providerData.some((p) => p.providerId === 'password')) {
        setVerificationUser(nextUser); setProfile(null); setLoading(false); return;
      }
      setVerificationUser(null);
      try {
        const snapshot = await getDoc(doc(firestore, 'users', nextUser.uid));
        if (snapshot.exists()) {
          const saved = snapshot.data() as Profile;
          setProfile(saved);
          setScreen(saved.onboardingCompleted ? 'dashboard' : 'onboarding');
        } else {
          setProfile(blankProfile(nextUser));
          setScreen('onboarding');
        }
      } catch (e) {
        setError(firebaseError(e));
        setScreen('onboarding');
        setProfile(blankProfile(nextUser));
      } finally { setLoading(false); }
    });
    return unsubscribe;
  }, []);

  const runAuth = async (action: () => Promise<unknown>, success?: string) => {
    setBusy(true); setError(''); setNotice('');
    try { await action(); if (success) setNotice(success); }
    catch (e) { setError(firebaseError(e)); }
    finally { setBusy(false); }
  };

  const socialLogin = (provider: 'google' | 'apple') => {
    const currentAuth = auth;
    if (!currentAuth) return;
    void runAuth(() => signInWithPopup(currentAuth, provider === 'google' ? googleProvider : appleProvider));
  };

  const submitAuth = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (!auth) return;
    const data = new FormData(event.currentTarget);
    const email = String(data.get('email') || '').trim();
    const password = String(data.get('password') || '');
    if (authMode === 'register') {
      await runAuth(async () => {
        const credential = await createUserWithEmailAndPassword(auth!, email, password);
        await sendEmailVerification(credential.user);
        setVerificationUser(credential.user);
        setNotice('Verification email sent. Verify your email before continuing.');
      });
    } else {
      await runAuth(() => signInWithEmailAndPassword(auth!, email, password));
    }
  };

  const resetPassword = async (email: string) => {
    if (!auth || !email) { setError('Enter your email address first.'); return; }
    await runAuth(() => sendPasswordResetEmail(auth!, email), 'Password reset email sent. Check your inbox.');
  };

  const saveProfile = async (next: Profile) => {
    if (!user || !db) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const clean = { ...next, displayName: next.displayName.trim(), homeCity: next.homeCity.trim(), bio: next.bio.trim(),
        interests: next.interests.slice(0, 6), preferredDestinations: next.preferredDestinations.slice(0, 8),
        onboardingCompleted: true, updatedAt: serverTimestamp() };
      if (clean.displayName.length < 2) throw new Error('Enter a name with at least two characters.');
      if (clean.homeCity.length < 2) throw new Error('Enter your home city.');
      if (clean.interests.length === 0) throw new Error('Choose at least one travel interest.');
      if (clean.preferredDestinations.length === 0) throw new Error('Choose at least one destination.');
      const ref = doc(db, 'users', user.uid);
      const existing = await getDoc(ref);
      await setDoc(ref, {
        ...clean,
        uid: user.uid,
        email: user.email || '',
        photoURL: user.photoURL || '',
        createdAt: existing.exists() ? existing.data().createdAt : serverTimestamp(),
      }, { merge: true });
      if (user.displayName !== clean.displayName) await updateProfile(user, { displayName: clean.displayName });
      setProfile({ ...clean, email: user.email || '', photoURL: user.photoURL || '' });
      setScreen('dashboard');
    } catch (e) { setError(firebaseError(e)); }
    finally { setBusy(false); }
  };

  const logout = () => {
    const currentAuth = auth;
    if (currentAuth) void runAuth(() => signOut(currentAuth));
  };

  const removeAccount = async () => {
    if (!user || !auth || !db) return;
    const accepted = window.confirm('Permanently delete your Roamly account and profile? This cannot be undone.');
    if (!accepted) return;
    await runAuth(async () => {
      const providerIds = user.providerData.map((item) => item.providerId);
      if (providerIds.includes('password')) {
        const password = window.prompt('Confirm your password to permanently delete your account:');
        if (!password) throw new Error('Account deletion cancelled.');
        if (!user.email) throw new Error('Your account email is unavailable. Sign in again and retry.');
        await reauthenticateWithCredential(user, EmailAuthProvider.credential(user.email, password));
      } else if (providerIds.includes('google.com')) {
        await reauthenticateWithPopup(user, googleProvider);
      } else if (providerIds.includes('apple.com')) {
        await reauthenticateWithPopup(user, appleProvider);
      }
      await deleteDoc(doc(db!, 'users', user.uid));
      await deleteUser(user);
    });
  };

  if (loading) return <div className="loading-screen"><LoaderCircle className="spin"/><span>Preparing your Roamly experience…</span></div>;

  if (!firebaseConfigured) return <SetupScreen />;
  if (verificationUser) return <VerificationScreen user={verificationUser} busy={busy} error={error} notice={notice}
    onResend={() => void runAuth(() => sendEmailVerification(verificationUser), 'Verification email sent again.')}
    onLogout={logout} />;

  return <>
    <Header user={user} profile={profile} showLandingLinks={screen === 'home' && !user}
      onLogin={() => { setAuthMode('login'); setScreen('auth'); }} onLogout={logout}
      onProfile={() => setScreen('profile')} onHome={() => setScreen(user ? (profile?.onboardingCompleted ? 'dashboard' : 'onboarding') : 'home')} />
    {screen === 'home' && !user && <Landing onStart={() => { setAuthMode('register'); setScreen('auth'); }} onLogin={() => { setAuthMode('login'); setScreen('auth'); }} />}
    {screen === 'auth' && !user && <AuthScreen mode={authMode} setMode={setAuthMode} busy={busy} error={error} notice={notice}
      onSubmit={submitAuth} onGoogle={() => socialLogin('google')} onApple={() => socialLogin('apple')}
      onBack={() => setScreen('home')} onReset={resetPassword} />}
    {screen === 'onboarding' && user && <Onboarding initial={profile || blankProfile(user)} busy={busy} error={error}
      onSave={saveProfile} onLogout={logout} />}
    {screen === 'dashboard' && user && profile && <Dashboard user={user} profile={profile} onEdit={() => setScreen('profile')} onLogout={logout} />}
    {screen === 'profile' && user && profile && <ProfileEditor profile={profile} busy={busy} error={error} onSave={async (p) => { await saveProfile(p); setScreen('profile'); }}
      onCancel={() => setScreen('dashboard')} onDelete={removeAccount} />}
    <Footer />
  </>;
}

function Header({ user, profile, showLandingLinks, onLogin, onLogout, onProfile, onHome }: {
  user: FirebaseUser | null; profile: Profile | null; showLandingLinks: boolean; onLogin: () => void; onLogout: () => void; onProfile: () => void; onHome: () => void;
}) {
  return <header className="site-header"><button className="wordmark" onClick={onHome} aria-label="Roamly home"><span className="brand-symbol">✳</span> roam<span>ly</span></button>
    {showLandingLinks && !user && <nav className="header-links" aria-label="Landing page sections"><a href="#how-it-works">How it works</a><a href="#why-roamly">Why Roamly</a></nav>}
    <div className="header-actions">{user ? <><button className="profile-pill" onClick={onProfile}>{profile?.photoURL ? <img src={profile.photoURL} /> : <span className="mini-avatar">{(profile?.displayName || user.email || 'R')[0].toUpperCase()}</span>}<span>{profile?.displayName || 'Your profile'}</span></button><button className="text-button" onClick={onLogout}>Log out</button></> : <><button className="text-button" onClick={onLogin}>Log in</button><button className="button button-dark button-small" onClick={onLogin}>Get started <ArrowRight size={15}/></button></>}</div>
  </header>;
}

function Landing({ onStart, onLogin }: { onStart: () => void; onLogin: () => void }) {
  return <main>
    <section className="hero-section">
      <div className="hero-copy"><div className="eyebrow"><span className="eyebrow-dot"/> A better way to go places</div>
        <h1>Find your way<br/><em>out there.</em></h1>
        <p>Plan journeys that feel like you. Meet people who share your curiosity. Make the trip matter as much as the destination.</p>
        <div className="hero-buttons"><button className="button button-dark" onClick={onStart}>Start your journey <ArrowRight size={17}/></button><button className="button button-quiet" onClick={onLogin}>I already have an account</button></div>
        <div className="hero-proof"><div className="proof-avatars"><span>R</span><span>M</span><span>A</span></div><span>Made for curious travellers, everywhere.</span></div>
      </div>
      <div className="hero-art"><div className="hero-image" role="img" aria-label="A mountain lake surrounded by dramatic green mountains"/><div className="floating-note note-top"><Compass size={17}/><span><b>Go a little further</b><small>Your next story is waiting</small></span></div><div className="floating-note note-bottom"><div className="note-icon"><Users size={18}/></div><span><b>Better together</b><small>Find your kind of people</small></span></div><div className="image-stamp">ROAM<br/>MORE <span>↗</span></div></div>
    </section>
    <section className="marquee-band"><span>LESS SCROLLING, MORE EXPLORING</span><i>✳</i><span>PLANS THAT FEEL PERSONAL</span><i>✳</i><span>GOOD PEOPLE, GREAT PLACES</span><i>✳</i></section>
    <section className="feature-section" id="why-roamly"><div className="section-intro"><div className="eyebrow">The Roamly feeling</div><h2>Travel is better when<br/>it feels like <em>your thing.</em></h2><p>From the first idea to the people you meet along the way, bring your journey together in one place.</p></div>
      <div className="feature-grid"><Feature icon={<Sparkles/>} number="01" title="Shape your journey" body="Start with an idea and build a trip around your pace, interests and budget."/><Feature icon={<Users/>} number="02" title="Find your people" body="Meet travellers who are excited about the same places and experiences."/><Feature icon={<Globe2/>} number="03" title="Keep it all together" body="Your travel identity and future adventures, organised in one home."/></div>
    </section>
    <section className="manifesto" id="how-it-works"><div><div className="eyebrow">A little less ordinary</div><h2>Don't just see<br/>somewhere. <em>Feel it.</em></h2></div><div className="manifesto-side"><p>Roamly is being built for people who want more from travel: more connection, more intention, and more stories worth telling.</p><button className="button button-light" onClick={onStart}>Build your traveller profile <ArrowRight size={16}/></button></div></section>
    <section className="closing-cta"><div className="eyebrow">Your next chapter starts here</div><h2>Ready when <em>you are.</em></h2><p>Create your traveller profile and make room for what's next.</p><button className="button button-dark" onClick={onStart}>Join Roamly <ArrowRight size={17}/></button></section>
  </main>;
}
function Feature({ icon, number, title, body }: { icon: React.ReactNode; number: string; title: string; body: string }) {
  return <article className="feature-card"><div className="feature-top"><span className="feature-icon">{icon}</span><span>{number}</span></div><h3>{title}</h3><p>{body}</p></article>;
}

function AuthScreen({ mode, setMode, busy, error, notice, onSubmit, onGoogle, onApple, onBack, onReset }: {
  mode: AuthMode; setMode: (m: AuthMode) => void; busy: boolean; error: string; notice: string;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void; onGoogle: () => void; onApple: () => void; onBack: () => void; onReset: (email: string) => void;
}) {
  const [email, setEmail] = useState('');
  return <main className="auth-wrap"><button className="back-link" onClick={onBack}><ArrowLeft size={16}/> Back to Roamly</button><section className="auth-card"><div className="auth-aside"><div className="eyebrow">Your next story starts here</div><h2>{mode === 'register' ? 'Make room for more.' : 'Welcome back.'}</h2><p>{mode === 'register' ? 'Create your account. Then tell us a little about the way you love to travel.' : 'Pick up where your curiosity left off.'}</p><div className="auth-aside-art"><span>✳</span><small>GO WHERE<br/>YOU GROW</small></div></div><div className="auth-form-side"><div className="auth-heading"><span className="eyebrow">ROAMLY ACCOUNT</span><h1>{mode === 'register' ? 'Create account' : 'Log in'}</h1><p>{mode === 'register' ? 'Start with the basics. Your traveller profile comes next.' : 'Good to have you back.'}</p></div>
    <div className="provider-buttons"><button className="provider-button" onClick={onGoogle} disabled={busy}><GoogleMark/> Continue with Google</button><button className="provider-button" onClick={onApple} disabled={busy}><AppleMark/> Continue with Apple</button></div>
    <div className="or-divider"><span/>or continue with email<span/></div>
    <form onSubmit={onSubmit} className="auth-fields"><label>Email address<input name="email" type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={(e) => setEmail(e.target.value)}/></label><label>Password<input name="password" type="password" minLength={mode === 'register' ? 8 : 1} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'} required/></label>
      {mode === 'login' && <button type="button" className="forgot-link" onClick={() => onReset(email)}>Forgot password?</button>}
      <button className="button button-dark auth-submit" disabled={busy}>{busy ? <LoaderCircle className="spin" size={17}/> : mode === 'register' ? 'Create account' : 'Log in'} <ArrowRight size={16}/></button></form>
    {error && <div className="alert alert-error">{error}</div>}{notice && <div className="alert alert-success">{notice}</div>}
    <p className="switch-auth">{mode === 'register' ? 'Already have an account?' : 'New to Roamly?'} <button onClick={() => setMode(mode === 'register' ? 'login' : 'register')}>{mode === 'register' ? 'Log in' : 'Create an account'}</button></p>
    <p className="legal-note">By continuing, you agree to Roamly's Terms and Privacy Policy. These documents will be published before public launch.</p>
  </div></section></main>;
}

function Onboarding({ initial, busy, error, onSave, onLogout }: { initial: Profile; busy: boolean; error: string; onSave: (p: Profile) => void; onLogout: () => void }) {
  const [form, setForm] = useState<Profile>(initial);
  const [step, setStep] = useState(0);
  useEffect(() => setForm(initial), [initial]);
  const update = (key: keyof Profile, value: string) => setForm((p) => ({ ...p, [key]: value }));
  const toggle = (key: 'interests' | 'preferredDestinations', value: string) => setForm((p) => ({ ...p, [key]: p[key].includes(value) ? p[key].filter((x) => x !== value) : [...p[key], value] }));
  const next = () => {
    if (step === 0 && (!form.displayName.trim() || !form.homeCity.trim())) return;
    if (step === 1 && form.interests.length === 0) return;
    if (step < 2) setStep(step + 1); else onSave(form);
  };
  return <main className="onboarding-wrap"><div className="onboarding-top"><span className="eyebrow">YOUR ROAMLY PROFILE</span><button className="text-button" onClick={onLogout}>Log out</button></div><section className="onboarding-card"><div className="onboarding-progress"><div className="progress-copy"><span>LET'S GET TO KNOW YOU</span><b>0{step + 1} <i>/ 03</i></b></div><div className="progress-track"><span style={{ width: `${(step + 1) / 3 * 100}%` }}/></div></div>
    {step === 0 && <div className="onboarding-content"><div className="step-icon"><UserRound/></div><div className="eyebrow">A little introduction</div><h1>Who are you, <em>traveller?</em></h1><p className="step-description">Give your travel identity a starting point. You can always update this later.</p><div className="form-grid"><label className="field-label full">What should we call you?<input value={form.displayName} onChange={(e) => update('displayName', e.target.value)} placeholder="Your name" maxLength={60}/></label><label className="field-label">Home city<input value={form.homeCity} onChange={(e) => update('homeCity', e.target.value)} placeholder="e.g. Bengaluru" maxLength={60}/></label><label className="field-label">Country<input value={form.country} onChange={(e) => update('country', e.target.value)} placeholder="Country" maxLength={60}/></label><label className="field-label full">A line about you <span className="optional">OPTIONAL</span><textarea value={form.bio} onChange={(e) => update('bio', e.target.value)} placeholder="I'm happiest somewhere new, with good food and a long trail…" maxLength={240}/></label></div></div>}
    {step === 1 && <div className="onboarding-content"><div className="step-icon"><Heart/></div><div className="eyebrow">Your kind of adventure</div><h1>What moves <em>you?</em></h1><p className="step-description">Choose the things you'd love to experience. Pick at least one.</p><div className="choice-grid">{interests.map(({label, icon: Icon}) => <button key={label} className={`choice-card ${form.interests.includes(label) ? 'chosen' : ''}`} onClick={() => toggle('interests', label)}><Icon/><span>{label}</span>{form.interests.includes(label) && <Check className="choice-check"/>}</button>)}</div><div className="form-grid compact"><label className="field-label">Travel style<select value={form.travelStyle} onChange={(e) => update('travelStyle', e.target.value)}>{['Solo travel','Group travel','Backpacking','Comfort-first','Open to anything'].map(x => <option key={x}>{x}</option>)}</select></label><label className="field-label">Travel pace<select value={form.travelPace} onChange={(e) => update('travelPace', e.target.value)}>{['Relaxed','Balanced','Packed'].map(x => <option key={x}>{x}</option>)}</select></label></div></div>}
    {step === 2 && <div className="onboarding-content"><div className="step-icon"><MapPin/></div><div className="eyebrow">Places on your mind</div><h1>Where to <em>next?</em></h1><p className="step-description">Choose destinations that interest you. These help shape your future Roamly experience.</p><div className="destination-choices">{destinations.map(x => <button key={x} className={`destination-choice ${form.preferredDestinations.includes(x) ? 'chosen' : ''}`} onClick={() => toggle('preferredDestinations', x)}>{x}{form.preferredDestinations.includes(x) && <Check size={15}/>}</button>)}</div><div className="form-grid compact"><label className="field-label">Preferred budget<select value={form.budgetRange} onChange={(e) => update('budgetRange', e.target.value)}>{['Budget','Mid-range','Premium','Flexible'].map(x => <option key={x}>{x}</option>)}</select></label><div className="profile-summary"><ShieldCheck size={18}/><span>Your profile is private to your account in this phase.</span></div></div></div>}
    {error && <div className="alert alert-error">{error}</div>}<div className="onboarding-actions"><button className="button button-quiet" onClick={() => step === 0 ? onLogout() : setStep(step - 1)}>{step === 0 ? 'Not now' : 'Back'}</button><button className="button button-dark" onClick={next} disabled={busy || (step === 2 && form.preferredDestinations.length === 0)}>{busy ? <LoaderCircle className="spin" size={17}/> : step === 2 ? 'Save my profile' : 'Continue'} <ArrowRight size={16}/></button></div>
  </section><p className="onboarding-footnote">Your profile belongs to you. You control what you share.</p></main>;
}

function Dashboard({ user, profile, onEdit, onLogout }: { user: FirebaseUser; profile: Profile; onEdit: () => void; onLogout: () => void }) {
  const greeting = profile.displayName.split(' ')[0] || 'traveller';
  return <main className="dashboard-wrap"><section className="welcome-panel"><div className="welcome-copy"><div className="eyebrow">YOUR ROAMLY SPACE</div><h1>Good to have you,<br/><em>{greeting}.</em></h1><p>Your traveller profile is ready. This is the beginning of a more connected way to explore.</p><button className="button button-dark" onClick={onEdit}>View your profile <ArrowRight size={16}/></button></div><div className="welcome-art"><div className="welcome-orbit orbit-one"/><div className="welcome-orbit orbit-two"/><Plane size={78}/><span>✳</span></div></section>
    <div className="dashboard-section-head"><div><div className="eyebrow">YOUR TRAVEL IDENTITY</div><h2>A little more about you.</h2></div><button className="text-button" onClick={onEdit}>Edit profile <ArrowRight size={15}/></button></div>
    <section className="profile-overview"><div className="profile-main"><div className="large-avatar">{profile.photoURL ? <img src={profile.photoURL} alt="Profile"/> : (profile.displayName[0] || 'R').toUpperCase()}</div><div><h3>{profile.displayName}</h3><p>{profile.homeCity}, {profile.country}</p><span className="account-email"><Mail size={13}/>{user.email}</span></div></div><p className="profile-bio">{profile.bio || 'A traveller with room for new stories.'}</p><div className="profile-tags">{profile.interests.map(x => <span key={x}>{x}</span>)}</div><div className="profile-meta"><span><b>Travel style</b>{profile.travelStyle}</span><span><b>Budget</b>{profile.budgetRange}</span><span><b>Pace</b>{profile.travelPace}</span></div></section>
    <section className="next-steps"><div className="next-step-icon"><Sparkles/></div><div><h3>Your next adventure is taking shape.</h3><p>We're building Roamly one thoughtful step at a time. Trip planning and traveller discovery will connect to your account in a later phase.</p></div><span className="coming-soon">COMING NEXT</span></section>
    <div className="dashboard-bottom"><span><ShieldCheck size={15}/> Signed in securely with Firebase</span><button className="text-button" onClick={onLogout}><LogOut size={15}/> Log out</button></div>
  </main>;
}

function ProfileEditor({ profile, busy, error, onSave, onCancel, onDelete }: { profile: Profile; busy: boolean; error: string; onSave: (p: Profile) => void; onCancel: () => void; onDelete: () => void }) {
  const [form, setForm] = useState(profile);
  const update = (key: keyof Profile, value: string) => setForm(p => ({...p, [key]: value}));
  const toggle = (key: 'interests' | 'preferredDestinations', value: string) => setForm(p => ({...p, [key]: p[key].includes(value) ? p[key].filter(x => x !== value) : [...p[key], value]}));
  return <main className="editor-wrap"><button className="back-link" onClick={onCancel}><ArrowLeft size={16}/> Back to profile</button><section className="editor-card"><div className="eyebrow">YOUR ACCOUNT</div><h1>Make it <em>yours.</em></h1><p className="step-description">Keep your traveller profile up to date.</p>
    <div className="form-grid"><label className="field-label">Display name<input value={form.displayName} onChange={e => update('displayName',e.target.value)} maxLength={60}/></label><label className="field-label">Home city<input value={form.homeCity} onChange={e => update('homeCity',e.target.value)} maxLength={60}/></label><label className="field-label">Country<input value={form.country} onChange={e => update('country',e.target.value)} maxLength={60}/></label><label className="field-label">Travel style<select value={form.travelStyle} onChange={e => update('travelStyle',e.target.value)}>{['Solo travel','Group travel','Backpacking','Comfort-first','Open to anything'].map(x=><option key={x}>{x}</option>)}</select></label><label className="field-label">Budget<select value={form.budgetRange} onChange={e => update('budgetRange',e.target.value)}>{['Budget','Mid-range','Premium','Flexible'].map(x=><option key={x}>{x}</option>)}</select></label><label className="field-label">Travel pace<select value={form.travelPace} onChange={e => update('travelPace',e.target.value)}>{['Relaxed','Balanced','Packed'].map(x=><option key={x}>{x}</option>)}</select></label><label className="field-label full">Bio<textarea value={form.bio} onChange={e => update('bio',e.target.value)} maxLength={240}/></label></div>
    <div className="eyebrow subsection-label">INTERESTS</div><div className="destination-choices">{interests.map(({label,icon:Icon})=><button key={label} className={`choice-card compact-choice ${form.interests.includes(label)?'chosen':''}`} onClick={()=>toggle('interests',label)}><Icon size={17}/>{label}</button>)}</div>
    <div className="eyebrow subsection-label">DESTINATIONS</div><div className="destination-choices">{destinations.map(x=><button key={x} className={`destination-choice ${form.preferredDestinations.includes(x)?'chosen':''}`} onClick={()=>toggle('preferredDestinations',x)}>{x}{form.preferredDestinations.includes(x)&&<Check size={15}/>}</button>)}</div>
    {error && <div className="alert alert-error">{error}</div>}<div className="onboarding-actions"><button className="button button-quiet" onClick={onCancel}>Cancel</button><button className="button button-dark" disabled={busy} onClick={()=>onSave(form)}>{busy?<LoaderCircle className="spin" size={17}/>: 'Save changes'} <Check size={16}/></button></div>
    <div className="danger-zone"><div><b>Delete your account</b><p>Permanently remove your Roamly account and profile.</p></div><button className="delete-button" onClick={onDelete}><Trash2 size={15}/> Delete account</button></div>
  </section></main>;
}

function VerificationScreen({ user, busy, error, notice, onResend, onLogout }: { user: FirebaseUser; busy: boolean; error: string; notice: string; onResend: () => void; onLogout: () => void }) {
  return <main className="verification-wrap"><section className="verification-card"><div className="step-icon"><Mail/></div><div className="eyebrow">ONE QUICK CHECK</div><h1>Check your <em>inbox.</em></h1><p>We sent a verification link to <b>{user.email}</b>. Verify your email, then sign in again to continue building your profile.</p>{error&&<div className="alert alert-error">{error}</div>}{notice&&<div className="alert alert-success">{notice}</div>}<button className="button button-dark" disabled={busy} onClick={onResend}>Resend verification email <ArrowRight size={16}/></button><button className="text-button" onClick={onLogout}>Back to login</button></section></main>;
}

function SetupScreen() {
  return <main className="setup-wrap"><section className="setup-card"><div className="step-icon"><SlidersHorizontal/></div><div className="eyebrow">ONE-TIME PROJECT SETUP</div><h1>Connect <em>Firebase.</em></h1><p>Roamly's production web app is ready for your Firebase web configuration. Add the values to <code>web/.env.local</code>, then restart the development server.</p><pre>{`VITE_FIREBASE_API_KEY=...\nVITE_FIREBASE_AUTH_DOMAIN=...\nVITE_FIREBASE_PROJECT_ID=roamly-production-40a79\nVITE_FIREBASE_MESSAGING_SENDER_ID=...\nVITE_FIREBASE_APP_ID=...`}</pre><p className="setup-hint">Use the Web App config from Firebase Project settings. Never add service-account private keys here.</p></section></main>;
}
function Footer() { return <footer className="site-footer"><button className="wordmark" onClick={() => window.scrollTo({top:0,behavior:'smooth'})}><span className="brand-symbol">✳</span> roam<span>ly</span></button><span>Go where you grow. © {new Date().getFullYear()} Roamly.</span><span>Built for the curious.</span></footer>; }
function GoogleMark() { return <svg viewBox="0 0 48 48" aria-hidden="true"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3A12 12 0 1 1 31 15.1l5.7-5.7A20 20 0 1 0 44 24c0-1.2-.1-2.4-.4-3.5Z"/><path fill="#FF3D00" d="m6.3 14.7 6.6 4.8A12 12 0 0 1 31 15.1l5.7-5.7A20 20 0 0 0 6.3 14.7Z"/><path fill="#4CAF50" d="M24 44a20 20 0 0 0 13.5-5.2l-6.2-5.2A12 12 0 0 1 12.7 28l-6.5 5A20 20 0 0 0 24 44Z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3a12 12 0 0 1-4 5.6l6.2 5.2A20 20 0 0 0 44 24c0-1.2-.1-2.4-.4-3.5Z"/></svg>; }
function AppleMark() { return <svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.7 12.8c0-2.2 1.8-3.3 1.9-3.4a4.2 4.2 0 0 0-3.3-1.8c-1.4-.1-2.7.8-3.4.8s-1.8-.8-3-.8a4.5 4.5 0 0 0-3.8 2.3c-1.6 2.8-.4 6.9 1.1 9.1.7 1.1 1.6 2.3 2.7 2.2 1.1 0 1.5-.7 2.9-.7s1.8.7 3 .7 2-1.1 2.7-2.2a10 10 0 0 0 1.2-2.5 3.9 3.9 0 0 1-2-3.7ZM14.4 6.1A4 4 0 0 0 15.3 3a4.1 4.1 0 0 0-2.8 1.4 3.8 3.8 0 0 0-.9 3 3.4 3.4 0 0 0 2.8-1.3Z"/></svg>; }
function firebaseError(error: unknown): string {
  const code = typeof error === 'object' && error && 'code' in error ? String((error as {code: string}).code) : '';
  const messages: Record<string,string> = {
    'auth/email-already-in-use': 'An account already exists with this email. Try logging in.',
    'auth/invalid-email': 'Enter a valid email address.',
    'auth/network-request-failed': 'Network connection failed. Check your internet and try again.',
    'auth/too-many-requests': 'Too many attempts. Wait a little before trying again.',
    'auth/weak-password': 'Choose a stronger password with at least 8 characters.',
    'auth/invalid-credential': 'Email or password is incorrect.',
    'auth/user-disabled': 'This account has been disabled.',
    'auth/popup-closed-by-user': 'The sign-in window was closed before completion.',
    'auth/popup-blocked': 'Your browser blocked the sign-in window. Allow pop-ups and try again.',
    'auth/unauthorized-domain': 'This website domain is not authorised in Firebase Authentication settings.',
    'auth/operation-not-allowed': 'This sign-in provider is not enabled in Firebase Authentication yet.',
    'auth/account-exists-with-different-credential': 'An account already exists with this email using another sign-in method.',
    'auth/requires-recent-login': 'For security, log out and sign in again before deleting your account.',
    'permission-denied': 'Firebase denied this operation. Check that the published Firestore rules match the setup guide.',
    'unavailable': 'Firebase is temporarily unavailable. Check your connection and try again.',
  };
  if (messages[code]) return messages[code];
  if (error instanceof Error) return error.message;
  return 'Something went wrong. Please try again.';
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
