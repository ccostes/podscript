import { useState, useEffect } from 'react'
import { useUser, useSupabaseClient } from '@supabase/auth-helpers-react'

export default function Profile({ session }) {
    const [responseJson, setResponseJson] = useState({})
    const invokeNewUser = async () => {
      setResponseJson({ loading: true })
      const { data, error } = await supabase.functions.invoke('new-user', {})
      if (error) alert(error)
      setResponseJson(data)
    }
    const supabase = useSupabaseClient()

    // useEffect(() => {
    //   // invokeNewUser();
    // }, []);

    return (
    <div className='container mx-auto grid place-content-center min-h-screen'>
      <p>Success! Your email has been confirmed and your subscription is now active!</p>
      <p>You will receive the latest episode shortly, and each new episode when they are available.</p>
      {/* <p>Oh hi there {session.user.email}</p>
      <button
        className="mt-2 rounded bg-green-500 py-2 px-4 font-bold text-white hover:bg-green-700"
        onClick={invokeNewUser}
      >
        Invoke Function
      </button>
      <div className="p-2">
        <h3 className="mb-2 text-3xl">Response</h3>
        <pre className="bg-gray-300 p-2	">{JSON.stringify(responseJson, null, 2)}</pre>
      </div>
      <button
        className='mt-4 p-2 pl-5 pr-5 bg-blue-500 text-gray-100 text-lg rounded-lg focus:border-4 border-blue-300'
        onClick={() => supabase.auth.signOut()}
      >
        Logout
      </button> */}
    </div>
  );
}