import { useState, useEffect, useRef } from 'react'
import { useUser, useSupabaseClient } from '@supabase/auth-helpers-react'
import Search from './Search';
import Card from './Card';

export default function Login() {
  const supabase = useSupabaseClient()
  const [email, setEmail] = useState('');
  const [searchSelection, setSearchSelection] = useState(null);
  const [searchFocus, setSearchFocus] = useState(false);
  const [loginResult, setLoginResult] = useState(null);
  const emailInputReference = useRef(null);
  
  const handleLogin = async (email, podcast) => {
    try {
      const user_metadata = {
        'podcast': {
          'apple_id': podcast.collectionId,
          'feed_url': podcast.feedUrl,
        }
      }
      const { error } = await supabase.auth.signInWithOtp({ 
        email: email,
        options: {
          data: { user_metadata } 
        }
      });
      if (error) throw error;
      // Signup complete!
      setLoginResult(true)
    } catch (error) {
      alert(error.error_description || error.message);
    }
  };
  
  function handleSearchSelect(podcast) {
    setSearchSelection(podcast);
    if(emailInputReference.current)
    {emailInputReference.current.focus();}
  }
  
  function handleResultSelect(){
    setSearchFocus(true);
    setSearchSelection(null);
  }
  
  function searchOrSelection(){
    if (!searchSelection || Object.keys(searchSelection).length == 0){
      // No selection, show search
      return (
        <Search results={[]} focus={searchFocus} handleSelect={handleSearchSelect}/>  
        )
    } else {
      // Show selected podcast
      return (
        <Card podcast={searchSelection} handleSelect={handleResultSelect} classes='rounded-xl' />
        )
    }
  }
  function emailInput() {
    if (searchSelection) {
      return (
        <div className='pt-2'>
          <input
          autoFocus
          className='mb-4 border-2 border-gray-500 rounded-xl p-4 w-full focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:border-transparent'
          type='email'
          name='email'
          placeholder='Your email'
          value={email}
          ref={emailInputReference}
          onChange={(e) => setEmail(e.target.value)}
          />
          <button
          onClick={(e) => {
            e.preventDefault();
            handleLogin(email, searchSelection);
          }}
          className='w-full p-2 pl-5 pr-5 bg-blue-500 text-gray-100 text-lg rounded-lg focus:border-4 border-blue-300'
          >
          <span>Subscribe!</span>
          </button>
        </div>
      )
    }
  }
  function signupOrResult(){
    if (!loginResult) {
      return (
        <div className='w-96 mx-auto'>
        {searchOrSelection()}
        {emailInput()}
        </div>
        );
    } else {
      return (
        <div className='mx-auto p-8 place-content-center text-center text-2xl font-raleway'>
          Signup Success!<br />Check your email for the verification link
        </div>
      )
    }
  }
     
return (
  <div>
    <div className='mx-auto p-8 place-content-center text-center text-5xl font-raleway'>
      <p className="p-2">Your Favorite Podcasts</p>
      <p className="">Now in your Inbox</p>
    </div> 
    {signupOrResult()}
  </div>
  );
}