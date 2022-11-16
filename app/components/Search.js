import React, { useEffect, useState, useRef } from 'react';
import SearchList from './SearchList';

function Search({ results, focus, handleSelect }) {
  const [searchField, setSearchField] = useState("");
  const [searchResults, setSearchResults] = useState(results);
  const [searchShow, setSearchShow] = useState(false);
  const inputReference = useRef(null);

  const handleChange = e => {
    setSearchField(e.target.value);
    if(e.target.value===""){
        setSearchShow(false);
    } else {
        setSearchShow(true);
    }
  };

  function searchList() {
    if (searchShow) {
        return (
          <SearchList podcasts={searchResults} handleSelect={handleResultSelected} />
        );
    }
  }

  function handleResultSelected(podcast) {
    setSearchShow(false);
    handleSelect(podcast)
  }

  useEffect(() => {
    if (focus) {
        inputReference.current.focus();
    }
  }, []);

  var _searchDelayTimer = null;
  function searchQueryChanged(event) {
    if(_searchDelayTimer) {
        clearTimeout(_searchDelayTimer);
        _searchDelayTimer = null;
    }

    _searchDelayTimer = setTimeout(searchQueryChangedCallback, 250);
  }

  var _searchInProgress = null;
  var _searchInProgressQuery = null;
  function searchQueryChangedCallback() {
    const searchBox = inputReference.current;
    console.log("Search Query Changed, value: " + searchBox.value);
    if (searchBox.value == _searchInProgressQuery) return;
    _searchInProgressQuery = searchBox.value;
    if(_searchInProgress) {
        _searchInProgress.abort();
        _searchInProgress = null;
    }
    
    if(_searchInProgressQuery.length < 3) {
        setSearchResults([]);
        return;
    }
    
    _searchInProgress = new XMLHttpRequest();
    _searchInProgress.open('GET', "https://itunes.apple.com/search?media=podcast&entity=podcast&term=" + encodeURIComponent(searchBox.value), true);
    _searchInProgress.onreadystatechange = function() {
        if (_searchInProgress.readyState == 4) {
            if (_searchInProgress.status == 200) {
                var decoded = false;
                try { decoded = JSON.parse(_searchInProgress.responseText); }
                catch (e) { console.log('JSON decoding error: ' + e + "\nResponse:\n\n" + _searchInProgress.responseText); }

                setSearchResults(decoded.results);
            } else {
                setSearchResults([])
                console.log("Query Error: " + _searchInProgress);
            }
            _searchInProgress = null;
        }
    };
    _searchInProgress.send(null);
    }

  return (
    <div className='w-96 place-self-center'>
      <div className="text-gray-500">
        <div class="w-full relative">
            <input 
                type="text" 
                class="w-full p-2 pl-8 rounded border border-gray-200 bg-gray-200 focus:bg-white focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:border-transparent" 
                placeholder="Search Podcasts" 
                onChange = {handleChange}
                ref={inputReference}
                autoComplete="off"
                onKeyUp={searchQueryChanged}
            />
            <svg class="w-4 h-4 absolute left-2.5 top-3.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
        </div>
      </div>
      {searchList()}
    </div>
  );
}

export default Search;